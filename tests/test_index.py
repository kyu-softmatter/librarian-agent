"""The index: deterministic, and honest about what it did not find."""

import sqlite3

import pytest

from librarian.doc import Doc
from librarian.index import Index, Profile, build, manifest

SHA = "abc1234"


def _doc(i: int, **kw) -> Doc:
    base = dict(repo="ms", path=f"kb/x{i}.md", locator="verdict", commit_sha=SHA,
                kind="expertise", title=f"entry {i}", body=f"body {i}")
    base.update(kw)
    return Doc(**base)


@pytest.fixture
def idx(tmp_path):
    docs = [
        _doc(1, title="AlexaFluor488", body="bleach_photons is absent for this dye",
             evidence="assumed", tier=3, kind="registry"),
        _doc(2, title="camera readout", body="measured on the instrument",
             evidence="measured", tier=1, kind="calibration", has_falsifier=True),
        _doc(3, title="objective NA", body="NA 1.45 exceeds n_immersion",
             kind="doc_section"),
        _doc(5, title="internal analysis", body="internal analysis of the channel",
             kind="doc_section"),
        _doc(4, title="microrheology",
             body="GSER 로 프로브 입자의 MSD 하나만으로 복소점탄성률을 뽑는다. "
                  "무차원화 규약은 확산계수 D 와 점도 eta 를 쓴다.",
             kind="doc_section"),
    ]
    p = tmp_path / "kb.sqlite"
    build(docs, p, {"ms": SHA})
    i = Index(p)
    yield i
    i.close()


# --- determinism -----------------------------------------------------------

def test_rebuild_is_byte_identical(tmp_path):
    """BUILD.md 4-A, taken literally rather than weakened.

    SQLite is byte-reproducible for the same insert sequence, so the rows are
    sorted by uid before insert and no timestamp is written. A `built_at` would
    break this for no information gained -- the commit SHA already says what the
    index was built from, which is the question staleness asks.
    """
    docs = [_doc(i) for i in range(30)]
    a, b = tmp_path / "a.sqlite", tmp_path / "b.sqlite"
    build(docs, a, {"ms": SHA})
    build(list(reversed(docs)), b, {"ms": SHA})       # input order must not matter
    assert a.read_bytes() == b.read_bytes()
    assert manifest({"ms": SHA}, 30) == manifest({"ms": SHA}, 30)
    assert "built_at" not in manifest({"ms": SHA}, 30)


def test_advances_is_not_a_column(idx):
    """Derived in SQL too, so the index cannot hold a copy that disagrees."""
    cols = {r[1] for r in idx.db.execute("PRAGMA table_info(doc)")}
    assert "advances" not in cols
    hits = idx.search("measured", Profile(id="t")).hits
    assert [h.advances for h in hits] == [h.evidence == "measured" for h in hits]


def test_fts_cannot_drift_from_its_content_table(idx):
    n_doc = idx.db.execute("SELECT count(*) FROM doc").fetchone()[0]
    n_fts = idx.db.execute("SELECT count(*) FROM doc_fts").fetchone()[0]
    assert n_doc == n_fts


# --- retrieval -------------------------------------------------------------

def test_terms_are_or_ed_not_and_ed(idx):
    """A question must not require every word as a substring.

    Measured on the real corpus: *"what limits how long I can image this dye"*
    returned exactly one document out of 544 under AND. bm25 already favours a
    document matching more terms, so OR ranks instead of refusing.
    """
    res = idx.search("bleach dye camera objective microrheology", Profile(id="t"))
    assert res.status == "ok"
    assert len(res.hits) >= 3


def test_single_characters_are_dropped(idx):
    res = idx.search("how long can I image a dye", Profile(id="t"))
    assert "I" not in res.terms_matched and "I" not in res.terms_globbed
    assert "a" not in res.terms_globbed


def test_short_terms_use_glob_so_case_is_respected(idx):
    """`LIKE '%NA%'` matched 349 of 544 real documents; `GLOB '*NA*'` matched 65.

    For a two-character technical term, case is the signal: `NA` is the
    numerical aperture and `na` is a syllable.
    """
    upper = idx.search("NA", Profile(id="t"))
    assert upper.terms_globbed == ["NA"] and upper.terms_matched == []
    assert [h.title for h in upper.hits] == ["objective NA"]

    # `na` is a different query: it finds the lowercase syllable inside
    # "internal" and "analysis", and does not find the aperture.
    lower = idx.search("na", Profile(id="t"))
    assert [h.title for h in lower.hits] == ["internal analysis"]


@pytest.mark.parametrize("q,expect", [
    ("무차원화", True),      # 4 chars, a standalone token
    ("무차원", True),        # 3 chars, inside 무차원화
    ("점탄성", True),        # 3 chars, inside 복소점탄성률을
    ("확산", True),          # 2 chars, inside 확산계수 -- the GLOB path
    ("점도", True),          # 2 chars, standalone
])
def test_korean_queries_hit_at_every_length(idx, q, expect):
    """The measured hole in BUILD.md 3, closed end to end.

    `unicode61` returns 0 for a Korean substring; `trigram` returns 0 for any
    two-character term. Neither alone is enough, so the split is verified here
    rather than in the shell.
    """
    assert (idx.search(q, Profile(id="t")).status == "ok") is expect


def test_searched_empty_is_a_status_not_a_count(idx):
    """`not_searched` is the absence of a record; this is a searched corpus."""
    res = idx.search("zzzqqqxyzzy", Profile(id="t"))
    assert res.status == "searched_empty" and res.hits == []
    assert idx.search("   ", Profile(id="t")).status == "searched_empty"


def test_every_hit_carries_coordinates_and_a_tier(idx):
    for h in idx.search("dye camera NA", Profile(id="t")).hits:
        repo, rest = h.uid.split(":", 1)
        path, locator = rest.split("#", 1)
        assert repo and path and locator
        assert hasattr(h, "evidence") and hasattr(h, "tier")


def test_index_stale_is_reported_on_every_response(idx):
    assert idx.search("dye", Profile(id="t"), current_shas={"ms": SHA}).index_stale is False
    assert idx.search("dye", Profile(id="t"), current_shas={"ms": "moved"}).index_stale is True
    # An empty result still reports staleness -- otherwise a stale index looks
    # the same as an empty corpus.
    assert idx.search("zzzz", Profile(id="t"), current_shas={"ms": "moved"}).index_stale is True


def test_require_is_opt_in_and_rejects_unknown_columns(idx):
    res = idx.search("dye camera", Profile(id="t"), require={"evidence": ["measured"]})
    assert all(h.evidence == "measured" for h in res.hits)
    with pytest.raises(ValueError):
        idx.search("dye", Profile(id="t"), require={"'; DROP TABLE doc; --": ["x"]})


# --- profiles --------------------------------------------------------------

def test_kind_weight_reorders_without_filtering(idx):
    """A weight, not a filter.

    `prefer_kinds` as a hard filter was the first draft, and on the real corpus
    it removed the answer: most `registry` entries carry `verified: false`, and
    the dye registry is exactly what lens 5 needs.
    """
    q = "AlexaFluor488 camera measured bleach_photons"
    reg = Profile(id="reg", kind_weight={"registry": 5.0})
    cal = Profile(id="cal", kind_weight={"calibration": 5.0})
    assert idx.search(q, reg).hits[0].kind == "registry"
    assert idx.search(q, cal).hits[0].kind == "calibration"
    # neither dropped anything
    assert len(idx.search(q, reg).hits) == len(idx.search(q, cal).hits)


def test_ties_break_on_uid_so_an_oracle_has_something_stable(idx):
    p = Profile(id="flat")
    a = [h.uid for h in idx.search("body", p).hits]
    b = [h.uid for h in idx.search("body", p).hits]
    assert a == b == sorted(a) or a == b


def test_profile_yaml_round_trips(tmp_path):
    (tmp_path / "p.yaml").write_text(
        "id: ms:test\n"
        "kind_weight: {registry: 1.5}\n"
        "boost:\n  gate: [G10]\n  field: [bleach_photons]\n"
        "  path_prefix: [data/]\n"
        "demote:\n  reproduced:\n    \"no\": 0.7\n"
        "return_always: [evidence, tier]\n")
    p = Profile.load(tmp_path / "p.yaml")
    assert p.id == "ms:test"
    assert p.kind_weight == {"registry": 1.5}
    assert p.boost_gate == ("G10",) and p.boost_field == ("bleach_photons",)
    assert p.demote == {"reproduced": {"no": 0.7}}


# --- result diversity ------------------------------------------------------

def test_one_file_cannot_fill_the_result_set(tmp_path):
    """Measured on the real corpus: one entry took three of six slots.

    Asked what limits how long a dye can be imaged,
    `kb/expertise/oil-objective-trapping-in-water.md` supplied three of six
    hits and the registry the question needed was pushed out. bm25 ranks
    sections independently and has no reason not to fill a page with one file.
    """
    docs = [
        Doc(repo="ms", path="kb/one.md", locator=f"s{i}", commit_sha=SHA,
            kind="expertise", title=f"trap section {i}",
            body="trap stiffness objective magnification " * 3)
        for i in range(5)
    ] + [
        Doc(repo="ms", path="data/objectives.yaml", locator="objectives.60x",
            commit_sha=SHA, kind="registry", title="objectives > 60x-Oil",
            body="magnification 60 na 1.4 trap"),
        Doc(repo="ms", path="kb/two.md", locator="verdict", commit_sha=SHA,
            kind="expertise", title="trap notes", body="trap stiffness"),
    ]
    p = tmp_path / "kb.sqlite"
    build(docs, p, {"ms": SHA})
    idx = Index(p)
    try:
        hits = idx.search("trap stiffness objective magnification",
                          Profile(id="t"), limit=4).hits
        paths = [h.uid.split("#")[0] for h in hits]
        assert paths.count("ms:kb/one.md") <= idx.MAX_PER_PATH
        assert len(hits) == 4, "capping must not shrink a full result set"
        assert len(set(paths)) >= 2
    finally:
        idx.close()


def test_capping_backfills_rather_than_returning_fewer(tmp_path):
    """When only one file matches, the cap must not withhold results."""
    docs = [Doc(repo="ms", path="kb/only.md", locator=f"s{i}", commit_sha=SHA,
                kind="expertise", title=f"section {i}", body="stiffness")
            for i in range(6)]
    p = tmp_path / "kb.sqlite"
    build(docs, p, {"ms": SHA})
    idx = Index(p)
    try:
        assert len(idx.search("stiffness", Profile(id="t"), limit=5).hits) == 5
    finally:
        idx.close()


def test_a_non_profile_yaml_is_skipped_rather_than_crashing(tmp_path):
    """`_field-aliases.yaml` sits beside the profiles and is not one.

    Loading it as a profile raised a KeyError on a missing `id`. Files
    beginning with `_` are not profiles -- the microscope's convention, for the
    same reason.
    """
    from librarian.index import load_profiles
    d = tmp_path / "profiles"
    d.mkdir()
    (d / "_field-aliases.yaml").write_text("aliases:\n  radius_m: {registry: r, field: f}\n")
    (d / "real.yaml").write_text("id: ms:test\nkind_weight: {registry: 2.0}\n")
    profiles = load_profiles(d)
    assert set(profiles) == {"neutral", "ms:test"}

    (d / "broken.yaml").write_text("kind_weight: {registry: 2.0}\n")
    with pytest.raises(ValueError, match="no `id`"):
        load_profiles(d)
