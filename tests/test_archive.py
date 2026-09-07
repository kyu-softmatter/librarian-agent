"""The acquisition archive reader: header-only, and loud about what it missed.

Four tests are marked `integration` because they import the microscope's own
parser from a checkout under `cache/`. The parser is imported rather than
copied -- a vendored copy that drifts from the one the microscope maintains is
worse than none, because the drift is silent -- and that makes the checkout a
real dependency rather than a convenience.

No real Micro-Manager file was available while this was written, so the
fixtures are synthetic and shaped after what the microscope's own parser
tolerates: MM 1.4 quotes its numbers, and neither generation guarantees
pretty-printing. The spec-derived arithmetic is verified here; the device tier
is not, which is what `unresolved` exists to say.
"""

import json
import textwrap

import pytest

from librarian.archive import (
    TAIL_BYTES,
    ArchiveError,
    Acquisition,
    camera_label,
    dump,
    extract,
    load_ms_parser,
    parse_folder_name,
    read_fragments,
    sample,
)


def write_mm(folder, frames=300, interval_ms=100, delivered_ms=130,
             camera="Pirme95B", elapsed=True):
    """A synthetic MM 1.4-shaped metadata.txt: quoted numbers, pretty-printed."""
    folder.mkdir(parents=True, exist_ok=True)
    lines = ["{", '  "Summary": {']
    for k, v in {
        "Interval_ms": interval_ms, "Frames": frames,
        "Width": 2400, "Height": 2400, "BitDepth": 12,
        "ComputerName": "TAKATORI-PC", "Core-Camera": camera,
        "Nosepiece-Label": "Nikon 60x Plan Apo",
    }.items():
        lines.append(f'    "{k}": "{v}",')
    lines[-1] = lines[-1].rstrip(",")
    lines.append("  },")
    for t in range(frames):
        lines.append(f'  "FrameKey-{t}-0-0": {{')
        if elapsed:
            lines.append(f'    "ElapsedTime-ms": "{t * delivered_ms}",')
        lines.append('    "Camera-Binning": "1"')
        lines.append("  },")
    lines[-1] = lines[-1].rstrip(",")
    lines.append("}")
    p = folder / "metadata.txt"
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


# --- the folder-name rules, fully specified in docs/02 section 7 -----------

@pytest.mark.parametrize("name,expect", [
    ("Las10", {"name_illum_level": 10.0}),
    ("Las488", {"name_wavelength_nm": 488.0}),
    ("Las555_5", {"name_wavelength_nm": 555.0, "name_illum_percent": 5.0}),
    ("Las555_5_ATPS_647", {"name_wavelength_nm": 555.0, "name_illum_percent": 5.0}),
    ("Las900", {"name_illum_level": 900.0}),          # outside 350-800
])
def test_las_tokens(name, expect):
    """An integer in 350-800 is a wavelength; anything else is a level.

    `Las555_5_ATPS_647` is the regression: the trailing guard was `\\b`, and an
    underscore is a word character, so the percentage went unparsed on exactly
    the names that carry one.
    """
    out = parse_folder_name(name)
    for k, v in expect.items():
        assert out[k] == v
    for k in ("name_wavelength_nm", "name_illum_percent", "name_illum_level"):
        if k not in expect:
            assert k not in out


def test_the_recorded_camera_typo_folds_to_one_name():
    """`Prime95B` vs `Pirme95B` in 20 acquisitions (docs/02 section 7)."""
    assert camera_label('"Core-Camera": "Pirme95B"') == "Prime95B"
    assert camera_label('"Core-Camera": "Prime95B"') == "Prime95B"
    assert camera_label('"Core-Camera": "Kinetix22"') is None


# --- reading three fragments, not the file ---------------------------------

def test_a_large_file_is_read_by_the_header_only(tmp_path):
    p = write_mm(tmp_path / "Las488", frames=6000)
    frag = read_fragments(p)
    assert frag.size_bytes > 4 * TAIL_BYTES
    assert frag.whole_file_read is False
    assert frag.bytes_read < frag.size_bytes / 3
    assert frag.head_reached_first_framekey is True
    # the head stops at the first FrameKey, so only frame 0 is in it
    assert frag.head.count('"FrameKey-') == 1


def test_a_short_file_is_read_whole(tmp_path):
    """Regression: the tail was empty below the tail size.

    The head stops at the first FrameKey, so leaving the tail empty lost the
    last timestamp on every short acquisition -- and with it the drop screen.
    """
    p = write_mm(tmp_path / "Las488", frames=50)
    frag = read_fragments(p)
    assert frag.size_bytes <= TAIL_BYTES
    assert frag.whole_file_read is True
    assert '"ElapsedTime-ms"' in frag.tail


def test_a_summary_larger_than_the_head_is_reported_not_truncated_silently(tmp_path):
    p = write_mm(tmp_path / "Las488", frames=6000)
    frag = read_fragments(p, head_bytes=200)
    assert frag.head_reached_first_framekey is False


# --- the drop screen -------------------------------------------------------

@pytest.mark.integration
def test_the_cheap_drop_screen(ms, tmp_path):
    """docs/02 section 7: the mean delivered interval exceeds the requested one
    exactly when frames went missing. It cannot say where or how many."""
    mm, _ = load_ms_parser(ms)
    p = write_mm(tmp_path / "Las555_5", frames=300, interval_ms=100, delivered_ms=130)
    a = extract(p, mm, root=tmp_path)
    assert a.interval_ms == 100 and a.frames == 300
    assert a.mean_delivered_interval_ms == pytest.approx(130.0)
    assert a.requested_fps == pytest.approx(10.0)
    assert a.measured_fps == pytest.approx(1000 / 130)
    assert a.frames_went_missing is True

    clean = write_mm(tmp_path / "Las488", frames=300, interval_ms=130, delivered_ms=130)
    assert extract(clean, mm, root=tmp_path).frames_went_missing is False


@pytest.mark.integration
def test_a_file_with_no_timestamps_is_recorded_not_skipped(ms, tmp_path):
    """MM 2.0's NDTiff carries no metadata.txt, so a dataset scans as zero frames.

    A silently absent row is indistinguishable from a clean acquisition, which
    is why docs/02 section 6 has a `parse_error` column.
    """
    mm, _ = load_ms_parser(ms)
    p = write_mm(tmp_path / "Las488", frames=20, elapsed=False)
    a = extract(p, mm, root=tmp_path)
    assert a.parse_error is not None and "NDTiff" in a.parse_error
    assert "drop_screen.no_timestamps" in a.unresolved
    assert a.acq_id and a.path                    # still a row


@pytest.mark.integration
def test_the_device_tier_is_reported_as_unresolved(ms, tmp_path):
    """The gap is a value in the dump rather than an absence from it."""
    mm, _ = load_ms_parser(ms)
    a = extract(write_mm(tmp_path / "Las488", frames=20), mm, root=tmp_path)
    assert any(u.startswith("device.") for u in a.unresolved)
    assert "device.objective_label" in a.unresolved
    assert a.raw_summary and '"Nosepiece-Label"' in a.raw_summary


# --- the sweep -------------------------------------------------------------

@pytest.mark.integration
def test_dump_is_deterministic_and_records_its_parser(ms, tmp_path):
    write_mm(tmp_path / "arc" / "Las488", frames=40)
    write_mm(tmp_path / "arc" / "Las555_5", frames=40)
    a, b = tmp_path / "a.jsonl", tmp_path / "b.jsonl"
    r1 = dump(tmp_path / "arc", a, ms)
    r2 = dump(tmp_path / "arc", b, ms)
    assert a.read_text() == b.read_text()
    assert r1["files"] == r2["files"] == 2

    header = json.loads(a.read_text().splitlines()[0])["_header"]
    assert header["parser"].endswith("compute/mm_metadata.py")
    assert header["parser_commit"]            # which commit the parser came from
    assert header["tail_bytes"] == TAIL_BYTES


def test_the_parser_is_imported_and_a_missing_checkout_says_so(tmp_path):
    """Not vendored. A copy that drifts from the one the microscope maintains is
    worse than none, because the drift is silent."""
    with pytest.raises(ArchiveError) as e:
        load_ms_parser(tmp_path / "not-a-checkout")
    assert "git clone" in str(e.value)


def test_sample_does_not_report_a_fraction_above_one(tmp_path):
    p = write_mm(tmp_path / "Las488", frames=40)
    rep = sample(p)
    assert rep["whole_file_read"] is True
    assert rep["fraction_read"] is None
    big = write_mm(tmp_path / "Las555_5", frames=6000)
    rep = sample(big)
    assert 0 < rep["fraction_read"] < 1
