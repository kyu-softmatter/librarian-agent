"""A profile is a claim about the repository it points into, and claims go stale.

`profiles/*.yaml` heads with *"read off the repository, not invented"* and names
the file each list came from. Nothing checked that, and one had already rotted:
`ms-lens5-photo-perturbation.yaml` boosted **G10** until 2026-09-15, six days
after MS removed the gate. Drift did not catch it because `librarian/drift.py`
reads MS's `docs/` against MS's code and never reads this repository's own
files -- so a profile is the one place a dead gate id could sit unnoticed.

It matters more than a stale comment. `boost.gate` changes which evidence a
caller gets back, and the profile-candidate design (`PLAN.md` 5.3) reads these
lists to say *which lens owns a term*. An owner list naming a retired gate is a
wrong answer with a citation attached, which is the one kind this repository is
built to not produce.
"""

from pathlib import Path

import pytest
import yaml

from librarian.gaps import gate_functions
from librarian.inputs import load_aliases, registry_keys, verify_aliases
from librarian.scan import scan

ROOT = Path(__file__).resolve().parent.parent
PROFILES = ROOT / "profiles"

pytestmark = pytest.mark.integration


def _neutral():
    from librarian.index import Profile
    return Profile(id="neutral")


_NEUTRAL = _neutral()


def _profiles() -> list[tuple[str, dict]]:
    out = []
    for p in sorted(PROFILES.glob("*.yaml")):
        if p.name.startswith("_"):          # _field-aliases.yaml is not a profile
            continue
        out.append((p.name, yaml.safe_load(p.read_text(encoding="utf-8"))))
    assert out, "there should be at least one profile"
    return out


def test_every_boosted_gate_is_declared_by_ms_code(ms):
    """A boost on a gate that no longer exists is silent: it just never fires."""
    live = {f.gate for f in gate_functions(ms)}
    assert "G10" not in live, "the fixture for this test is that G10 is gone"

    for name, prof in _profiles():
        if not str(prof.get("id", "")).startswith("ms:"):
            continue
        boosted = set((prof.get("boost") or {}).get("gate") or [])
        dead = sorted(boosted - live)
        assert not dead, f"{name} boosts gates MS code does not declare: {dead}"


def test_every_boosted_field_could_ever_fire(ms, tmp_path):
    """A boost is checked by what it can raise, not by what declares it.

    **Two strengths, because the two kinds of term fail differently.** A
    retired gate is still discussed in prose -- `docs/04` §6 keeps G10's
    formulas and explains the removal -- so presence in the corpus would not
    have caught G10. Gate ids are therefore checked against the code above.

    A field is the other way round. `n_medium` is declared by no registry:
    `optics/components.py` computes it as `IMMERSION_N[self.immersion]`, a
    lookup keyed by a registry field, and lens 4 is right to boost it because
    that is what `kb/expertise/sample-medium-refractive-index` is about. The
    defect worth catching is narrower and operational: **a boost term no
    indexed document carries can never raise anything.** It is not wrong, it
    is inert, and inert is indistinguishable from considered.

    Two earlier universes were both too small and both blamed the profile:
    registry keys alone failed on nine of lens 4's fields, and adding the
    fields gates read still failed on `n_medium` and `working_distance`.
    """
    from librarian.gaps import gaps as compute_gaps
    from librarian.index import Index, build
    from librarian.links import extract

    keys = registry_keys(ms)
    # Filtered by repo, the way `librarian.cli._alias_findings` does it. Checked
    # against every indexed repository instead, an alias naming MS's
    # `data/particles.yaml` is reported broken the moment BD -- which has no
    # `data/` -- joins the build. That check answered a question nobody asked.
    aliases = {leaf: a for leaf, a in
               load_aliases(PROFILES / "_field-aliases.yaml").items()
               if a.get("repo") == "ms"}
    assert aliases, "no ms aliases found; the repo key or the file moved"
    assert verify_aliases(aliases, keys) == [], "an alias has gone stale"

    rep = scan(ms)
    p = tmp_path / "kb.sqlite"
    build(rep.docs, p, {"ms": rep.sha},
          extract(rep.docs, rep.repo_files, rep.source_text), compute_gaps(ms))
    idx = Index(p)
    try:
        for name, prof in _profiles():
            if not str(prof.get("id", "")).startswith("ms:"):
                continue
            for fld in sorted((prof.get("boost") or {}).get("field") or []):
                if fld in aliases:
                    continue
                hits = idx.search(fld, _NEUTRAL, limit=1).hits
                assert hits, (
                    f"{name} boosts {fld!r}, which no indexed document "
                    f"carries -- the boost can never fire")
    finally:
        idx.close()


def test_kind_weights_name_only_kinds_that_exist():
    """An unlisted kind scores 1.0, so a misspelled one is a weight that never
    applies -- and it looks identical to a weight that was considered and set."""
    from librarian.doc import KINDS

    for name, prof in _profiles():
        weighted = set((prof.get("kind_weight") or {}))
        unknown = sorted(weighted - set(KINDS))
        assert not unknown, f"{name} weights kinds that do not exist: {unknown}"


# --- profile candidates (PLAN.md 5.3) ---------------------------------------

def _index(ms, tmp_path):
    from librarian.gaps import gaps as compute_gaps
    from librarian.index import Index, build
    from librarian.links import extract
    rep = scan(ms)
    p = tmp_path / "kb.sqlite"
    build(rep.docs, p, {"ms": rep.sha},
          extract(rep.docs, rep.repo_files, rep.source_text), compute_gaps(ms))
    return Index(p)


def _loaded():
    from librarian.index import load_profiles
    return load_profiles(PROFILES)


def test_candidates_land_on_the_lens_that_declares_the_question(ms, tmp_path):
    """The acceptance criterion, and it is the same shape as BUILD.md 4-B.

    One profile cannot show that candidate selection does anything: what has to
    hold is that two questions over the same corpus point at **different**
    owners. So both directions are asserted, and each with its own vocabulary.
    """
    idx = _index(ms, tmp_path)
    profs = _loaded()
    try:
        optics = idx.profile_candidates(
            "which objective and immersion for a deep chamber", profs)
        assert optics, "an optics question should point somewhere"
        assert optics[0].profile == "ms:lens-4-sample-optics"

        photo = idx.profile_candidates(
            "is the illumination dose too high for this exposure", profs)
        assert photo, "a dose question should point somewhere"
        assert photo[0].profile == "ms:lens-5-photo-perturbation"

        assert optics[0].profile != photo[0].profile
    finally:
        idx.close()


def test_a_candidate_cites_the_agent_file_and_not_the_profile(ms, tmp_path):
    """Rule 2. A profile listing a term is this repository describing itself.

    `kb_search` reports which profiles exist and what each weights; that does
    not license a claim about ownership. The licence is MS's own
    `.claude/agents/`, at a locator that `kb_get` resolves.
    """
    idx = _index(ms, tmp_path)
    profs = _loaded()
    try:
        cands = idx.profile_candidates("coverslip thickness and immersion", profs)
        assert cands
        for c in cands:
            assert c.because.startswith("ms:.claude/agents/"), c.because
            assert "profiles/" not in c.because
            assert idx.get(c.because) is not None, "the citation must resolve"
            assert c.matched_terms, "a candidate has to say what licensed it"
    finally:
        idx.close()


def test_nothing_is_applied_to_the_hits(ms, tmp_path):
    """Rule 1, asserted where it could actually break.

    The hits under `neutral` have to be byte-identical whether or not the
    candidates were computed. If they ever differ, retrieval has narrowed to a
    profile nobody declared -- the failure decision 31 names, and the one thing
    about this mechanism that could not be seen from the outside.
    """
    from librarian.index import NEUTRAL
    idx = _index(ms, tmp_path)
    profs = _loaded()
    q = "coverslip thickness for the oil objective"
    try:
        bare = idx.search(q, NEUTRAL, limit=10)
        with_c = idx.search(q, NEUTRAL, limit=10, profiles=profs)
        assert [h.uid for h in bare.hits] == [h.uid for h in with_c.hits]
        assert [h.score for h in bare.hits] == [h.score for h in with_c.hits]
        assert bare.profile_candidates == []
        assert with_c.profile_candidates
        assert with_c.as_dict()["candidates_applied"] is False
    finally:
        idx.close()


def test_a_profile_with_no_agent_file_is_never_a_candidate(ms, tmp_path):
    """Rule 4. `neutral` has no lens, so it has nothing to cite.

    An empty candidate list is the right answer for such a profile, not a gap
    to fill by relaxing rule 2 -- which is also why `human:*` roles will not
    appear here when they land (PLAN.md 3.5).
    """
    idx = _index(ms, tmp_path)
    profs = _loaded()
    try:
        assert profs["neutral"].lens is None
        cands = idx.profile_candidates("objective immersion coverslip dose", profs)
        assert cands, "the lens profiles should still be found"
        assert "neutral" not in {c.profile for c in cands}
    finally:
        idx.close()


def test_every_lens_profile_is_reachable_by_its_own_declaration(ms, tmp_path):
    """A profile no question can point at is a profile nobody will declare.

    Asserted as a correspondence rather than a list: it holds for the profiles
    that exist now and for the ones that land later, and it is what fails if a
    profile's `lens` number stops matching the agent file's own.
    """
    idx = _index(ms, tmp_path)
    profs = _loaded()
    try:
        lenses = {p.id for p in profs.values() if p.lens is not None}
        assert lenses, "there should be lens profiles"
        owners = idx._ownership_docs()
        for pid in sorted(lenses):
            prof = profs[pid]
            key = f"{pid.split(':', 1)[0]}:lens-{prof.lens}"
            assert key in owners, (
                f"{pid} declares lens {prof.lens} and no agent file in the "
                f"index declares that lens -- nothing could cite it")
    finally:
        idx.close()


def test_a_stopword_never_licenses_a_candidate(ms, tmp_path):
    """The defect that made the first implementation useless, pinned.

    An `owns` section is prose, so `can`, `this` and `the` occur in it as
    ordinary words. Matched as one OR-combined query the way `search` does it,
    *"how long can I image this dye before it bleaches"* was licensed for
    lens 5 by `can` and `this` -- the right answer for a reason that says
    nothing, which is worse than no answer because it reads as evidence.
    """
    idx = _index(ms, tmp_path)
    profs = _loaded()
    try:
        for q in ("can this the", "what seed did that run use"):
            assert idx.profile_candidates(q, profs) == [], q
        for c in idx.profile_candidates(
                "the illumination dose for this exposure", profs):
            assert not (set(c.matched_terms) & {"the", "this", "for"}), c.matched_terms
    finally:
        idx.close()


def test_an_inflected_word_does_not_reach_the_declaration(ms, tmp_path):
    """The known limit, measured rather than assumed -- and it returns nothing.

    `_fts_expr` quotes a term as a phrase, so trigram matching needs a
    contiguous substring: `bleach` finds `photobleaching`, `bleaches` does not.
    Decision 7 rules out the stemmer that would bridge them, so the inflected
    question gets **no candidate** rather than a guess. Pinned because the
    tempting fix -- loosening the match until `bleaches` lands somewhere -- is
    how a mechanism starts returning plausible owners for invisible reasons.
    """
    idx = _index(ms, tmp_path)
    profs = _loaded()
    try:
        assert idx.profile_candidates(
            "how long can I image this dye before it bleaches", profs) == []
        stemmed = idx.profile_candidates("bleach dose for this dye", profs)
        assert stemmed and stemmed[0].profile == "ms:lens-5-photo-perturbation"
    finally:
        idx.close()
