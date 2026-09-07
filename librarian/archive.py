"""The acquisition archive: sample one file, then dump 2,343 headers.

The archive lives in `D:\\data` on the lab PC, outside every repository. The
microscope designed a quantitative index for it -- `kb/envelope.sqlite`,
`docs/02-knowledge-base.md` sections 1 and 6 -- and never built it. Its own
parser says so in as many words:

    This is **not** the L1 indexer of docs/02-knowledge-base.md -- that one
    reads headers only (Summary + first FrameKey + tail) and builds a SQLite
    envelope across all 2,343 acquisitions.
        -- compute/mm_metadata.py

This module is the missing half, in the reversible form: a dump that can be
carried off the lab PC, rather than Librarian installed on it permanently.

## Three fragments, not 44 MB

`docs/02` section 7 fixes the read: `Summary` + the first `FrameKey` + a 96 kB
tail. The head is read once up to the first `FrameKey` and the tail by seek, so
a multi-hundred-MB file is never materialised.

## The parser is imported, not copied

`compute/mm_metadata.py` already tolerates what the files actually do -- MM 1.4
quotes numbers, neither generation guarantees pretty-printing, and both write
the same two tokens so the dual schema needs no branching. Copying that here
would create a second copy to drift from, which is the microscope's and the
simulator's shared debt in miniature. So it is imported from `cache/ms`, and the
commit it was imported from is recorded in the dump.

## What it cannot know yet

No real metadata file has been read while writing this. The five Summary fields
below are safe because the microscope's regexes were written against real files;
the device tier is **not** -- its key names and nesting are unverified. So every
row carries `unresolved`, the list of fields that were looked for and not found,
and the whole Summary is preserved verbatim in `raw_summary`. One sample file
turns that list into the diff to apply.

    librarian archive-sample <one metadata.txt>     # do this first
    librarian archive-dump  D:\\data --out dump.jsonl
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterator, Optional

HEAD_BYTES = 256 * 1024      #: enough to reach the first FrameKey in a pretty-printed file
TAIL_BYTES = 96 * 1024       #: docs/02 section 7
SCHEMA = "librarian.acquisition/0.1"

#: `"Key":` names in the head. A provisional basis for the fingerprint -- the
#: spec asks for the device-label set plus a camera chip/serial hash, and
#: narrowing this to exactly that needs a sample to confirm the nesting.
_KEY_RE = re.compile(r'"([A-Za-z][A-Za-z0-9 _.\-]{1,60})"\s*:')
_FRAMEKEY = re.compile(r'"FrameKey-\d+-\d+-\d+"')
_ELAPSED = re.compile(r'"ElapsedTime-ms"\s*:\s*"?(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"?')

#: `Prime95B` vs `Pirme95B` in 20 acquisitions (docs/02 section 7).
CAMERA_ALIASES = {
    "pirme95b": "Prime95B",
    "prime95b": "Prime95B",
}

#: `Las10` = level, `Las488` = wavelength, `Las555_5` = 555 nm at 5 %.
# The trailing guard is `(?!\d)` and not `\b`: in `Las555_5_ATPS_647` the
# underscore is a word character, so `\b` does not hold between `5` and `_` and
# the percentage went unparsed.
_LAS = re.compile(r"(?i)\bLas(\d+)(?:_(\d+(?:\.\d+)?))?(?!\d)")
WAVELENGTH_RANGE = (350, 800)     #: "an integer in 350-800 is a wavelength"


class ArchiveError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# the microscope's parser, imported
# --------------------------------------------------------------------------

def load_ms_parser(cache_ms: Path):
    """Load `compute/mm_metadata.py` from a microscope checkout, by file path.

    Returns `(module, commit_sha)`.

    **Loaded from its path, not by putting the checkout on `sys.path`.** The
    microscope has its own `mcp_server/` package, so prepending its root
    shadowed this repository's -- `import mcp_server` resolved to the
    microscope's and six tests broke at collection. The same shadowing that made
    this repository call its own folder `mcp_server` instead of `mcp` reappears
    in the other direction, at run time.

    A single-file load is also what the dependency actually is: that file imports
    nothing but the standard library.

    Refuses rather than falling back to a copy. A vendored parser that drifts
    from the one the microscope maintains is worse than no parser, because the
    drift is silent.
    """
    cache_ms = Path(cache_ms)
    target = cache_ms / "compute" / "mm_metadata.py"
    if not target.exists():
        raise ArchiveError(
            f"{target} not found. Clone the microscope first:\n"
            f"  git clone --depth 1 "
            f"https://github.com/kyu-softmatter/agentic-microscope.git {cache_ms}"
        )

    spec = importlib.util.spec_from_file_location("_ms_mm_metadata", target)
    if spec is None or spec.loader is None:
        raise ArchiveError(f"cannot load {target}")
    module = importlib.util.module_from_spec(spec)
    # Registered under a private name before execution. `dataclasses` resolves
    # string annotations through `sys.modules[cls.__module__]`, and the file
    # uses `from __future__ import annotations`, so without this the first
    # `@dataclass` raises. A private name cannot shadow anything, which is the
    # difference from putting the checkout on `sys.path`.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    sha = ""
    try:
        sha = subprocess.run(["git", "-C", str(cache_ms), "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
    except Exception:
        pass
    return module, sha


# --------------------------------------------------------------------------
# the three fragments
# --------------------------------------------------------------------------

@dataclass
class Fragments:
    """What was read, and how much of the file it was."""
    path: str
    size_bytes: int
    head: str
    tail: str
    head_reached_first_framekey: bool
    first_framekey: Optional[str] = None

    @property
    def bytes_read(self) -> int:
        return len(self.head.encode("utf-8", "replace")) + \
               len(self.tail.encode("utf-8", "replace"))

    @property
    def whole_file_read(self) -> bool:
        """True for a file at or under the tail size, which is read entire.

        Reported rather than folded into a fraction: head and tail overlap in
        that case, so the ratio exceeds 1 and reads as a bug.
        """
        return self.size_bytes <= TAIL_BYTES


def read_fragments(path: Path, head_bytes: int = HEAD_BYTES,
                   tail_bytes: int = TAIL_BYTES) -> Fragments:
    """Head up to the first FrameKey, and the tail by seek. Never the whole file.

    `head_reached_first_framekey` is reported rather than assumed. A Summary
    larger than `head_bytes` would otherwise truncate silently, and a truncated
    Summary looks exactly like a sparse one.
    """
    path = Path(path)
    size = path.stat().st_size
    with open(path, "rb") as fh:
        raw_head = fh.read(head_bytes)
        if size > tail_bytes:
            fh.seek(size - tail_bytes)
            raw_tail = fh.read(tail_bytes)
        else:
            # A file at or under the tail size is read whole -- 96 kB, so the
            # cost is nothing. Leaving the tail empty here lost the last
            # timestamp on every short acquisition, and with it the drop
            # screen, because the head stops at the first FrameKey.
            fh.seek(0)
            raw_tail = fh.read()
    head = raw_head.decode("utf-8", "replace")
    tail = raw_tail.decode("utf-8", "replace")

    m = _FRAMEKEY.search(head)
    if m:
        # Keep the Summary plus the first FrameKey block, and no more.
        nxt = _FRAMEKEY.search(head, m.end())
        head = head[: nxt.start()] if nxt else head
    return Fragments(path=str(path), size_bytes=size, head=head, tail=tail,
                     head_reached_first_framekey=bool(m),
                     first_framekey=m.group(0) if m else None)


# --------------------------------------------------------------------------
# one acquisition
# --------------------------------------------------------------------------

@dataclass
class Acquisition:
    schema: str = SCHEMA
    acq_id: str = ""
    path: str = ""
    size_bytes: int = 0

    # verified: the microscope's own regexes, written against real files
    interval_ms: Optional[float] = None
    frames: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bit_depth: Optional[int] = None

    # measured from the fragments
    first_elapsed_ms: Optional[float] = None
    last_elapsed_ms: Optional[float] = None
    mean_delivered_interval_ms: Optional[float] = None
    measured_fps: Optional[float] = None
    requested_fps: Optional[float] = None
    frames_went_missing: Optional[bool] = None

    # provisional
    system_fingerprint: Optional[str] = None
    fingerprint_basis: str = "summary_key_set"
    camera_label: Optional[str] = None

    # parsed from the folder name -- fully specified in docs/02 section 7
    name_wavelength_nm: Optional[float] = None
    name_illum_percent: Optional[float] = None
    name_illum_level: Optional[float] = None
    name_tags: list[str] = field(default_factory=list)

    raw_summary: str = ""
    unresolved: list[str] = field(default_factory=list)
    parse_error: Optional[str] = None


#: Device-tier fields `docs/02` section 6 declares and this draft cannot fill
#: without a sample. Listed so the gap is a value in the dump rather than an
#: absence in it.
DEVICE_TIER_WANTED = (
    "camera", "camera_chip", "objective_label", "intermediate_mag", "binning",
    "roi_x", "roi_y", "roi_w", "roi_h", "readout_rate", "camera_gain",
    "exposure_ms", "filter_cube", "filter_wheel", "light_path",
    "shutter_device", "illum_device", "illum_line", "illum_percent",
    "channel_name",
)


def parse_folder_name(name: str) -> dict[str, Any]:
    """`Las10` = level, `Las488` = wavelength, `Las555_5` = 555 nm at 5 %.

    The discriminator is the spec's: an integer in 350-800 is a wavelength.
    """
    out: dict[str, Any] = {"name_tags": []}
    for m in _LAS.finditer(name):
        n, pct = float(m.group(1)), m.group(2)
        if WAVELENGTH_RANGE[0] <= n <= WAVELENGTH_RANGE[1]:
            out["name_wavelength_nm"] = n
            if pct is not None:
                out["name_illum_percent"] = float(pct)
        else:
            out["name_illum_level"] = n
    out["name_tags"] = sorted({t for t in re.split(r"[^A-Za-z0-9.]+", name) if t})
    return out


def fingerprint(head: str) -> str:
    """A stable identity for the setup, from the Summary's key set.

    **Not the spec's fingerprint yet.** `docs/02` section 7 asks for the
    device-label set plus a camera chip/serial hash, and explicitly warns that
    distinguishing by PC name gets it wrong. The key set discriminates setups
    and is computable without knowing the nesting; narrowing it is what the
    sample is for.
    """
    keys = sorted({m.group(1) for m in _KEY_RE.finditer(head)
                   if not m.group(1).startswith("FrameKey")})
    return hashlib.sha256("\n".join(keys).encode()).hexdigest()[:16]


def camera_label(head: str) -> Optional[str]:
    """Canonical camera name, with the recorded typo folded in."""
    for token in re.findall(r'"([A-Za-z0-9_\- ]*95[Bb][^"]*)"', head):
        key = re.sub(r"[^a-z0-9]", "", token.lower())
        for alias, canon in CAMERA_ALIASES.items():
            if alias in key:
                return canon
    return None


def extract(path: Path, mm, root: Optional[Path] = None) -> Acquisition:
    """One acquisition, from its header fragments.

    A file that yields nothing is **recorded, not skipped.** MM 2.0's NDTiff
    format carries no `metadata.txt` at all, so such a dataset scans as zero
    frames -- and a silently absent row is indistinguishable from a clean one.
    `docs/02` section 6 has a `parse_error` column for exactly this.
    """
    path = Path(path)
    rel = str(path.relative_to(root)) if root else str(path)
    acq = Acquisition(acq_id=hashlib.sha256(rel.encode()).hexdigest()[:12], path=rel)

    try:
        frag = read_fragments(path)
    except OSError as e:
        acq.parse_error = f"unreadable: {e}"
        return acq

    acq.size_bytes = frag.size_bytes
    acq.raw_summary = frag.head
    acq.system_fingerprint = fingerprint(frag.head)
    acq.camera_label = camera_label(frag.head)

    if not frag.head_reached_first_framekey:
        acq.unresolved.append("first_framekey_not_in_head")

    try:
        hints = mm.read_summary_hints(path)
        acq.interval_ms = hints.interval_ms
        acq.frames = hints.frames
        acq.width = hints.width
        acq.height = hints.height
        acq.bit_depth = hints.bit_depth
    except Exception as e:                          # a parse failure is a value
        acq.parse_error = f"summary: {type(e).__name__}: {e}"

    for name in ("interval_ms", "frames", "width", "height", "bit_depth"):
        if getattr(acq, name) is None:
            acq.unresolved.append(f"summary.{name}")

    head_times = [float(m.group(1)) for m in _ELAPSED.finditer(frag.head)]
    tail_times = [float(m.group(1)) for m in _ELAPSED.finditer(frag.tail)]
    acq.first_elapsed_ms = head_times[0] if head_times else None
    acq.last_elapsed_ms = tail_times[-1] if tail_times else None

    # The cheap drop screen, docs/02 section 7: the mean delivered interval
    # exceeds the requested one exactly when frames went missing. It cannot say
    # **where** or **how many** -- that needs every timestamp, which is
    # compute/drops.py and a full read.
    if (acq.first_elapsed_ms is not None and acq.last_elapsed_ms is not None
            and acq.frames and acq.frames > 1):
        span = acq.last_elapsed_ms - acq.first_elapsed_ms
        acq.mean_delivered_interval_ms = span / (acq.frames - 1)
        if acq.mean_delivered_interval_ms > 0:
            acq.measured_fps = 1000.0 / acq.mean_delivered_interval_ms
        if acq.interval_ms:
            acq.requested_fps = 1000.0 / acq.interval_ms if acq.interval_ms else None
            acq.frames_went_missing = acq.mean_delivered_interval_ms > acq.interval_ms
    else:
        acq.unresolved.append("drop_screen.no_timestamps")

    acq.__dict__.update(parse_folder_name(path.parent.name))
    acq.unresolved += [f"device.{f}" for f in DEVICE_TIER_WANTED]
    if not head_times and not tail_times and acq.parse_error is None:
        acq.parse_error = ("no ElapsedTime-ms in header or tail -- possibly "
                           "NDTiff, which has no metadata.txt")
    return acq


# --------------------------------------------------------------------------
# the sweep
# --------------------------------------------------------------------------

def dump(root: Path, out: Path, cache_ms: Path,
         limit: Optional[int] = None) -> dict[str, Any]:
    """Every acquisition under `root`, one JSON object per line.

    Sorted by path, so a repeated sweep produces the same file.
    """
    mm, sha = load_ms_parser(cache_ms)
    root = Path(root)
    files = list(mm.iter_metadata_files(root))
    if limit:
        files = files[:limit]

    n_err = 0
    unresolved_counts: dict[str, int] = {}
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        header = {"schema": SCHEMA, "root": str(root), "files": len(files),
                  "parser": "agentic-microscope compute/mm_metadata.py",
                  "parser_commit": sha,
                  "head_bytes": HEAD_BYTES, "tail_bytes": TAIL_BYTES}
        fh.write(json.dumps({"_header": header}, ensure_ascii=False) + "\n")
        for p in files:
            acq = extract(p, mm, root=root)
            if acq.parse_error:
                n_err += 1
            for u in acq.unresolved:
                unresolved_counts[u] = unresolved_counts.get(u, 0) + 1
            fh.write(json.dumps(asdict(acq), ensure_ascii=False) + "\n")

    return {"files": len(files), "parse_errors": n_err,
            "parser_commit": sha, "out": str(out),
            "unresolved": dict(sorted(unresolved_counts.items(),
                                      key=lambda kv: -kv[1]))}


def sample(path: Path, out: Optional[Path] = None) -> dict[str, Any]:
    """The three fragments of one file, verbatim, for reading with human eyes.

    Do this before the sweep. The device tier's key names are unverified, so a
    sweep run first would apply a guessed parser 2,343 times.
    """
    frag = read_fragments(Path(path))
    report = {
        "path": frag.path,
        "size_bytes": frag.size_bytes,
        "bytes_read": frag.bytes_read,
        "whole_file_read": frag.whole_file_read,
        "fraction_read": (None if frag.whole_file_read or not frag.size_bytes
                          else round(frag.bytes_read / frag.size_bytes, 6)),
        "head_reached_first_framekey": frag.head_reached_first_framekey,
        "first_framekey": frag.first_framekey,
        "summary_keys": sorted({m.group(1) for m in _KEY_RE.finditer(frag.head)})[:200],
        "elapsed_in_head": len(_ELAPSED.findall(frag.head)),
        "elapsed_in_tail": len(_ELAPSED.findall(frag.tail)),
        "fingerprint": fingerprint(frag.head),
        "camera_label": camera_label(frag.head),
        "folder": Path(frag.path).parent.name,
        "folder_parsed": parse_folder_name(Path(frag.path).parent.name),
    }
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(report, indent=2, ensure_ascii=False)
            + "\n\n===== HEAD (Summary + first FrameKey) =====\n" + frag.head
            + "\n\n===== TAIL (last 96 kB) =====\n" + frag.tail,
            encoding="utf-8")
        report["written"] = str(out)
    return report
