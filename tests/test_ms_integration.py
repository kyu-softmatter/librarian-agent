"""Against the real repositories. Phase 0's exit condition lives here.

`PLAN.md` 7 Phase 0 states it: the drift report must **rediscover the two
defects a human found by hand**. A tool that cannot find those is not yet doing
anything, so they are asserted rather than described.
"""

import pytest

from librarian.drift import drift
from librarian.gaps import gaps, gate_functions
from librarian.scan import CANDIDATES, scan

pytestmark = pytest.mark.integration


# --- adapters ---------------------------------------------------------------

def test_every_candidate_file_yields_a_document(ms):
    rep = scan(ms)
    assert rep.per_source and all(n > 0 for n in rep.per_source.values())
    dropped = [f for f in rep.findings if f.check == "file_produced_nothing"]
    assert dropped == [], f"{len(dropped)} candidate files produced nothing"


def test_no_error_findings_and_no_coordinate_collisions(ms):
    rep = scan(ms)
    assert [f for f in rep.findings if f.severity == "error"] == []
    assert len({d.uid for d in rep.docs}) == len(rep.docs)


def test_candidate_enumeration_is_independent_of_the_adapters(ms):
    """The coverage check has to come from outside, or it checks nothing.

    An adapter asserting its own count would pass while silently dropping a
    folder -- which is how BD's `tools/kb.py` reported 0 for 126 entries.
    """
    assert set(CANDIDATES) == {"ms_kb", "ms_data", "ms_docs", "ms_agents"}
    for name, enumerate_ in CANDIDATES.items():
        assert enumerate_(ms), f"{name} enumerated no candidate files"


def test_only_measurements_advance(ms):
    docs = scan(ms).docs
    assert all(d.evidence == "measured" for d in docs if d.advances)
    assert any(d.advances for d in docs), "no measured value found at all"


# --- gaps: v1's primary product --------------------------------------------

def test_the_two_known_blockers_are_found(ms):
    """Both are stated by MS in prose; here they are derived from the files.

    `docs/07` Phase 0 calls `power_at_sample_mw` *"the largest effect, still the
    top blocker"*, and `photo/gate.py` says `bleach_photons` is absent for every
    dye. Neither string is read by this code.
    """
    rows = gaps(ms)
    by_field: dict[tuple[str, str], list] = {}
    for g in rows:
        by_field.setdefault((g.registry, g.field), []).append(g)

    bleach = by_field[("data/fluorophores.yaml", "bleach_photons")]
    assert len(bleach) == 17 and not any(g.present for g in bleach)
    assert bleach[0].gate == "G10"

    power = by_field[("data/light_sources.yaml", "power_at_sample_mw")]
    assert power and not any(g.present for g in power)


def test_gates_are_read_from_their_own_docstrings(ms):
    fns = gate_functions(ms)
    ids = {f.gate for f in fns}
    assert {"G10", "G15", "G20"} <= ids
    # optics states its checks as questions and carries no gate id, so it
    # contributes nothing -- the reason G2/G3/G4 show up as drift below.
    assert "optics" not in {f.module for f in fns}


# --- drift: the Phase 0 exit condition -------------------------------------

def test_ms_gates_declared_with_a_threshold_but_never_implemented(ms):
    subjects = {f.subject for f in drift(ms, "ms")
                if f.check == "gate_declared_not_implemented"}
    assert subjects == {"ms:G2", "ms:G3", "ms:G4"}


def test_the_exemplar_challenge_entry_cannot_itself_be_challenged(ms):
    """`kb/expertise/oil-objective-trapping-in-water.md` carries no falsifier.

    research-topic README 2.2 holds this entry up as *"a challenge that was
    upheld"* -- the model case for the whole retirement mechanism. It has
    `supersedes: null` and a `review_after`, and no falsification section, so by
    `kb-schema.md` 4.7 it is not challengeable. Five of the six entries beside
    it carry one.
    """
    subjects = {f.subject for f in drift(ms, "ms") if f.check == "falsifier_missing"}
    assert subjects == {"ms:kb/expertise/oil-objective-trapping-in-water.md"}


def test_bd_index_defects_are_rediscovered(bd):
    """PLAN.md 7 Phase 0's exit condition, asserted.

    Both defects were found by reading. Finding them again by tool is what makes
    the tool worth having -- and finding *only* them is what makes the report
    readable.
    """
    findings = drift(bd, "bd")
    checks = {f.check for f in findings}
    assert "generator_missing" in checks
    assert "declared_count_mismatch" in checks

    detail = next(f.detail for f in findings if f.check == "declared_count_mismatch")
    assert "40" in detail and "42" in detail

    gen = next(f.detail for f in findings if f.check == "generator_missing")
    assert "docs/tools/wiki_index.py" in gen

    # No noise: BD's roadmap mentions the microscope's gates in prose, and a
    # prose mention is not a declaration.
    assert [f for f in findings if f.check == "gate_declared_not_implemented"] == []


# --- search: the Phase 1 acceptance criterion -------------------------------

def _index(ms, tmp_path):
    from librarian.index import Index, build
    rep = scan(ms)
    p = tmp_path / "kb.sqlite"
    build(rep.docs, p, {"ms": rep.sha})
    return Index(p), rep.sha


def test_the_real_corpus_rebuilds_byte_identically(ms, tmp_path):
    from librarian.index import build
    rep = scan(ms)
    a, b = tmp_path / "a.sqlite", tmp_path / "b.sqlite"
    build(rep.docs, a, {"ms": rep.sha})
    build(rep.docs, b, {"ms": rep.sha})
    assert a.read_bytes() == b.read_bytes()
    assert a.stat().st_size > 0


def test_the_two_lens_profiles_return_different_answers(ms, tmp_path):
    """BUILD.md 4-B: identical top three means the profile is decorative.

    The two lenses consume different corpora on purpose -- lens 5 owns
    `bleach_photons` and G10, lens 4 owns G15-G19 and the captured priors on
    immersion media, coverslip thickness and medium refractive index -- so one
    question has to land in different places.
    """
    from librarian.index import load_profiles
    from pathlib import Path

    profiles = load_profiles(Path(__file__).resolve().parent.parent / "profiles")
    p5 = profiles["ms:lens-5-photo-perturbation"]
    p4 = profiles["ms:lens-4-sample-optics"]

    idx, sha = _index(ms, tmp_path)
    try:
        q = "what limits how long I can image this dye"
        top5 = [h.uid for h in idx.search(q, p5, limit=3, current_shas={"ms": sha}).hits]
        top4 = [h.uid for h in idx.search(q, p4, limit=3, current_shas={"ms": sha}).hits]

        assert len(top5) == len(top4) == 3
        assert set(top5).isdisjoint(top4), f"profiles agree: {top5}"
        assert all("kb/literature" in u for u in top5)
        assert all("kb/expertise" in u for u in top4)
    finally:
        idx.close()


def test_a_registry_entry_is_reachable_by_name(ms, tmp_path):
    from librarian.index import load_profiles
    from pathlib import Path

    profiles = load_profiles(Path(__file__).resolve().parent.parent / "profiles")
    idx, sha = _index(ms, tmp_path)
    try:
        res = idx.search("AlexaFluor488 bleach_photons",
                         profiles["ms:lens-5-photo-perturbation"], limit=5,
                         current_shas={"ms": sha})
        uids = [h.uid for h in res.hits]
        assert "ms:data/fluorophores.yaml#fluorophores.AlexaFluor488" in uids
        # and the tier travels with it, so nothing can be mistaken for measured
        assert all(h.evidence == "measured" for h in res.hits if h.advances)
    finally:
        idx.close()


def test_a_two_character_query_survives_the_real_corpus(ms, tmp_path):
    """`LIKE` matched 349 of 544 documents here; `GLOB` matches 65."""
    from librarian.index import Profile
    idx, sha = _index(ms, tmp_path)
    try:
        res = idx.search("NA", Profile(id="t"), limit=5, current_shas={"ms": sha})
        assert res.status == "ok" and res.terms_globbed == ["NA"]
        n_glob = idx.db.execute(
            "SELECT count(*) FROM doc WHERE body GLOB '*NA*'").fetchone()[0]
        n_like = idx.db.execute(
            "SELECT count(*) FROM doc WHERE body LIKE '%NA%'").fetchone()[0]
        assert n_glob < n_like / 3
    finally:
        idx.close()
