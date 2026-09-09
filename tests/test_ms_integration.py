"""Against the real repositories. Phase 0's exit condition lives here.

`PLAN.md` 7 Phase 0 states it: the drift report must **rediscover the two
defects a human found by hand**. A tool that cannot find those is not yet doing
anything, so they are asserted rather than described.
"""

import pytest

from librarian.drift import drift
from librarian.gaps import gaps, gate_functions
from adapters import ADAPTERS
from librarian.scan import CANDIDATES, scan, sources_for

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

    **Asserted as a correspondence, not as a list.** Naming the four MS sources
    here meant that adding BD's three failed this test rather than the thing it
    protects, and a test that has to be edited every time a source is added
    stops being read. What matters is that no adapter runs without an
    independent enumeration to check it against.
    """
    assert set(CANDIDATES) == set(ADAPTERS)
    for name in sources_for(ms):
        assert CANDIDATES[name](ms), f"{name} enumerated no candidate files"


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

def test_ms_gates_whose_code_never_names_them(ms):
    """G2/G3/G4 are implemented and untraceable, which is not the same defect.

    They were reported as `gate_declared_not_implemented` at error severity,
    and that claim was wrong: `optics/gate.py` enforces all three thresholds --
    `spectral_collection()`, `excitation_blocking_od()` against
    `LIMITS["blocking_od"]`, `LIMITS["crosstalk"]` -- exactly as
    `docs/04-decision-engine.md` says it does. What is true is narrower: the
    file states its checks as questions and writes no gate id, so nothing in
    code says which gate is which.

    Left as an error it made drift's non-zero exit meaningless for MS, which is
    the cost of reporting a traceability gap as a missing implementation.
    """
    findings = drift(ms, "ms")
    assert [f for f in findings if f.check == "gate_declared_not_implemented"] == []

    gates = [f for f in findings if f.check == "gate_not_traceable_to_code"]
    assert {f.subject for f in gates} == {"ms:G2", "ms:G3", "ms:G4"}
    assert {f.severity for f in gates} == {"warn"}
    # The report has to say where the implementation is, or it is the same
    # unfalsifiable complaint with a softer severity.
    assert all("optics.gate.evaluate" in f.detail for f in gates)


def test_every_ms_claim_entry_can_now_be_challenged(ms):
    """The finding was reported, and then it was fixed at the source.

    `kb/expertise/oil-objective-trapping-in-water.md` carried no falsifier,
    which mattered because research-topic README 2.2 holds that entry up as *"a
    challenge that was upheld"* -- the model case for the whole retirement
    mechanism -- while by `kb-schema.md` 4.7 it was the one entry in its folder
    that could not itself be challenged. It gained a `## Falsification
    conditions` section in MS `c147438`, so the count is zero.

    Asserting zero rather than deleting this test, because a check nobody
    exercises against the real repository stops being trusted, and because
    zero is the state a source repository is supposed to reach. Detection of a
    missing falsifier is still covered by
    `test_falsifier_convention_is_set_by_the_majority`, which builds the case
    synthetically and does not depend on MS staying defective.
    """
    subjects = {f.subject for f in drift(ms, "ms") if f.check == "falsifier_missing"}
    assert subjects == set()


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
    """The index as `reindex` builds it -- docs, links and gaps.

    Building only the documents left `kb_supplies` with no coverage rows, so a
    test of it passed vacuously against an index the CLI never produces.
    """
    from librarian.gaps import gaps as compute_gaps
    from librarian.index import Index, build
    from librarian.links import extract
    rep = scan(ms)
    links = extract(rep.docs, rep.repo_files, rep.source_text)
    p = tmp_path / "kb.sqlite"
    build(rep.docs, p, {"ms": rep.sha}, links, compute_gaps(ms))
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

        # The two land in different corpora. Asserted on the leading hit rather
        # than on all three: an earlier version pinned all three to one folder,
        # which encoded a result set from before per-file capping existed, and
        # broke when capping let a second source in -- an improvement failing a
        # test is the test's fault.
        assert "kb/literature" in top5[0]
        assert "kb/expertise" in top4[0]

        # And no single file fills a result set.
        for top in (top5, top4):
            files = [u.split("#")[0] for u in top]
            assert max(files.count(f) for f in files) <= idx.MAX_PER_PATH
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


# --- the input closure, on the real repository ------------------------------

def test_trap_stiffness_inputs_resolve_where_the_repository_declares_them(ms, tmp_path):
    """The worked example: what is needed to compute trap stiffness here.

    Objective list, laser power per setting, sample refractive index -- the
    three things an agent asks for. Two resolve structurally; the one that does
    not is the interesting answer.
    """
    from pathlib import Path

    from librarian.inputs import recipe

    idx, sha = _index(ms, tmp_path)
    try:
        r = recipe(ms, "radial_stiffness_n_per_m", index=idx,
                   aliases_path=Path(__file__).resolve().parent.parent
                   / "profiles" / "_field-aliases.yaml")
        assert r is not None
        assert r.location == "ms:trapping/goa.py#radial_stiffness_n_per_m"
        leaves = {l.path: l for l in r.leaves}

        # the objective list, which is what the question is parameterised over
        na = leaves["beam.na"]
        assert na.status == "ready"
        assert na.supplied_by[0]["registry"] == "data/objectives.yaml"
        assert na.supplied_by[0]["filled"] == na.supplied_by[0]["total"] == 6

        # a radius is not a diameter and the units differ, so this needs the alias
        rad = leaves["bead.radius_m"]
        assert rad.status == "ready" and rad.via_alias
        assert rad.supplied_by[0]["field"] == "diameter_um"

        # the refractive index is a captured prior, not a registry field, so it
        # arrives as a candidate -- found by searching what declares it, since
        # `n` is one character
        n = leaves["medium.n"]
        assert n.status == "unresolved"
        assert any("sample-medium-refractive-index" in c for c in n.candidates)
        assert "medium" in n.candidate_query

        # and the laser power is the one the instrument cannot supply
        assert leaves["power_w"].status == "unresolved"
        assert any("tweezers-first-light" in c for c in leaves["power_w"].candidates)
    finally:
        idx.close()


def test_the_trap_laser_power_field_is_blocked_everywhere(ms, tmp_path):
    """`power_at_sample_mw` is empty for all six sources, `Trap` among them."""
    idx, _ = _index(ms, tmp_path)
    try:
        out = idx.supplies("power_at_sample_mw")
        assert out["status"] == "blocked"
        assert out["coverage"][0]["filled"] == 0
        assert any(e["entry"].endswith(".Trap") for e in out["entries"])
    finally:
        idx.close()


def test_the_recorded_aliases_all_still_point_at_something(ms):
    """A stale alias is a finding, so the suite fails when one goes stale."""
    from pathlib import Path

    from librarian.inputs import load_aliases, registry_keys, verify_aliases
    aliases = load_aliases(Path(__file__).resolve().parent.parent
                           / "profiles" / "_field-aliases.yaml")
    assert aliases, "the alias file should not be empty"
    assert verify_aliases(aliases, registry_keys(ms)) == []
