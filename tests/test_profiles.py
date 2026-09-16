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
    aliases = load_aliases(PROFILES / "_field-aliases.yaml")
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
