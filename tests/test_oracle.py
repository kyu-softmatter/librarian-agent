"""Fixture F9: an oracle really catches a regression.

BUILD.md §2 · FEEDBACK.md §5. **The pass condition is that something fails** --
create one oracle, break the profile on purpose, and the run must go red. Stay
green and the oracle is an unwired checker, which is BD's recorded failure:
`tools/kb.py` pointed at a renamed path and *"simply reported 'run-less
knowledge 0' for 126 existing entries."*

So the shape of this file is unusual on purpose. `test_f9_*` asserts a **red**
result, and a bug that made every oracle vacuously pass would show up here as a
failure rather than as a green suite.

Offline, over a corpus built in the test, because F9 is about the mechanism
being wired -- not about the microscope's current ranking. The integration test
at the end runs whatever oracles are actually committed.
"""

import json
from pathlib import Path

import pytest

from librarian.doc import Doc
from librarian.index import Index, Profile, build
from librarian.oracle import (PromotionError, build_oracle, check_promotable,
                              promote, run, run_all)

ROOT = Path(__file__).resolve().parent.parent
ORACLES = ROOT / "kb" / "08-retrieval" / "oracles"

QUERY = "coverslip thickness for the oil objective"
WANTED = "ms:kb/expertise/coverslip-thickness-in-use.md#verdict"
DECOY = "ms:docs/06-pitfalls.md#coverslip"
DATE = "2026-09-15"


@pytest.fixture
def corpus(tmp_path):
    """Two documents that answer the same words, and one profile that prefers
    the right one. That preference is the thing an oracle guards."""
    docs = [
        Doc(repo="ms", path="kb/expertise/coverslip-thickness-in-use.md",
            locator="verdict", commit_sha="s1", kind="expertise",
            evidence="measured", tier=1, has_falsifier=True,
            title="what coverslip thickness does this lab mount on",
            body="170 um. The coverslips in use are the 170 um ones, and the "
                 "oil objective is corrected for exactly that thickness."),
        Doc(repo="ms", path="docs/06-pitfalls.md", locator="coverslip",
            commit_sha="s1", kind="doc_section",
            title="pitfalls -- coverslip",
            body="A coverslip thickness mismatch costs resolution; the oil "
                 "objective is the one that notices. Coverslip, coverslip."),
    ]
    p = tmp_path / "kb.sqlite"
    build(docs, p, {"ms": "s1"})
    return Index(p)


def _profiles(expertise: float):
    """`expertise` is the weight under test: raise it and the entry wins, drop
    it and the `docs/` section does."""
    return {"ms:lens-4-sample-optics": Profile(
        id="ms:lens-4-sample-optics", lens=4,
        kind_weight={"expertise": expertise, "doc_section": 1.0})}


def _sessions():
    """Two sessions, same citation, two distinct index states."""
    return [
        {"query": QUERY, "caller_profile": "ms:lens-4-sample-optics",
         "verdict": "useful", "cited": [WANTED], "index_sha": {"ms": "aaa1111"},
         "_id": "ret-aaaa1111"},
        {"query": QUERY, "caller_profile": "ms:lens-4-sample-optics",
         "verdict": "useful", "cited": [WANTED], "index_sha": {"ms": "bbb2222"},
         "_id": "ret-bbbb2222"},
    ]


# --- F9 ---------------------------------------------------------------------

def test_f9_an_oracle_catches_a_profile_regression(corpus, tmp_path):
    """**The fixture. Read the last assertion first: it requires a failure.**

    One oracle, promoted from two sessions under a profile that ranks the
    expertise entry first. Then the weight is inverted -- the same corpus, the
    same query, a profile that now prefers the `docs/` section -- and the
    oracle has to go red.

    If it stayed green, the oracle would be asserting nothing, and every future
    oracle built the same way would be asserting nothing too. That is why this
    is the exit condition for the folder rather than a nice-to-have.
    """
    good = _profiles(expertise=2.0)
    written = promote(tmp_path / "oracles", _sessions(), corpus, good, DATE,
                      approved_by_a_person=True, query_may_be_published=True)
    oracle = json.loads(written.path.read_text(encoding="utf-8"))

    # It measures the rank it actually saw, rather than asserting a chosen one.
    assert oracle["observed_ranks"][WANTED] == 1
    assert oracle["within_top"] == 1

    before = run(corpus, oracle, good)
    assert before.ok, f"the oracle must pass as promoted: {before}"

    # Break the profile on purpose: the decoy now outranks the entry.
    broken = _profiles(expertise=0.1)
    after = run(corpus, oracle, broken)

    assert not after.ok, (
        "F9 FAILED: the oracle stayed green after the profile was broken, so "
        "it asserts nothing. This is the unwired-checker failure mode.")
    assert after.missing == [WANTED]
    assert "REGRESSED" in str(after)


def test_f9_the_regression_is_reported_as_a_rank_and_not_a_boolean(corpus, tmp_path):
    """*How far* it slipped is what says where the fix goes. A boolean sends a
    reader to the profile with no idea whether the entry fell to 2 or vanished."""
    good = _profiles(expertise=2.0)
    w = promote(tmp_path / "oracles", _sessions(), corpus, good, DATE,
                approved_by_a_person=True, query_may_be_published=True)
    oracle = json.loads(w.path.read_text(encoding="utf-8"))

    slipped = run(corpus, {**oracle, "within_top": 1}, _profiles(expertise=0.1))
    assert slipped.ranks[WANTED] is None      # outside the asserted window
    widened = run(corpus, {**oracle, "within_top": 5}, _profiles(expertise=0.1))
    assert widened.ranks[WANTED] == 2, "it fell to second, and the report says so"
    assert widened.ok, "within a wider window the same slip is not a regression"


def test_a_deleted_profile_is_an_error_and_never_a_skip(corpus, tmp_path):
    """A skipped oracle is indistinguishable from a passing one, which is the
    whole of BD's `tools/kb.py` failure."""
    good = _profiles(expertise=2.0)
    w = promote(tmp_path / "oracles", _sessions(), corpus, good, DATE,
                approved_by_a_person=True, query_may_be_published=True)
    oracle = json.loads(w.path.read_text(encoding="utf-8"))
    with pytest.raises(PromotionError, match="unwired checker"):
        run(corpus, oracle, {})


# --- promotion refuses ------------------------------------------------------

def test_one_index_state_is_not_enough(corpus, tmp_path):
    """*"One is indistinguishable from chance."*"""
    one = _sessions()[:1]
    assert any("two distinct index_sha" in u for u in check_promotable(one))
    with pytest.raises(PromotionError, match="two distinct index_sha"):
        promote(tmp_path / "o", one, corpus, _profiles(2.0), DATE,
                approved_by_a_person=True, query_may_be_published=True)


def test_a_failure_record_is_not_an_oracle(corpus, tmp_path):
    bad = [{**s, "verdict": "wrong_ranking"} for s in _sessions()]
    with pytest.raises(PromotionError, match="failure record"):
        promote(tmp_path / "o", bad, corpus, _profiles(2.0), DATE,
                approved_by_a_person=True, query_may_be_published=True)


def test_approval_cannot_be_supplied_by_code(corpus, tmp_path):
    """The flag is a person's assertion. Passing `False` is what an automated
    caller has, and it is refused with the loop named."""
    with pytest.raises(PromotionError, match="self-confirming loop"):
        promote(tmp_path / "o", _sessions(), corpus, _profiles(2.0), DATE,
                approved_by_a_person=False, query_may_be_published=True)


def test_publishing_the_query_is_a_separate_judgment(corpus, tmp_path):
    """Collapsing the two would hide the second. An oracle carries its raw
    query and `oracles/` is committed, so promoting one publishes it."""
    with pytest.raises(PromotionError, match="publishes the query"):
        promote(tmp_path / "o", _sessions(), corpus, _profiles(2.0), DATE,
                approved_by_a_person=True, query_may_be_published=False)


def test_sessions_that_disagree_are_not_averaged(corpus, tmp_path):
    a, b = _sessions()
    with pytest.raises(PromotionError, match="not a summary of several"):
        build_oracle([a, {**b, "query": "a different question"}],
                     corpus, _profiles(2.0))


def test_a_citation_the_search_cannot_reproduce_is_refused(corpus, tmp_path):
    """Refused at promotion rather than written and left to fail forever."""
    ghost = [{**s, "cited": ["ms:kb/expertise/absent.md#verdict"]}
             for s in _sessions()]
    with pytest.raises(PromotionError, match="cannot reproduce"):
        promote(tmp_path / "o", ghost, corpus, _profiles(2.0), DATE,
                approved_by_a_person=True, query_may_be_published=True)


# --- the committed oracles --------------------------------------------------

def _real_index(ms, tmp_path):
    from librarian.gaps import gaps as compute_gaps
    from librarian.links import extract
    from librarian.scan import scan
    rep = scan(ms)
    p = tmp_path / "kb.sqlite"
    build(rep.docs, p, {"ms": rep.sha},
          extract(rep.docs, rep.repo_files, rep.source_text), compute_gaps(ms))
    return Index(p)


@pytest.mark.integration
def test_f9_on_the_real_corpus_and_the_real_profile(ms, tmp_path):
    """F9 again, against what is actually committed rather than a fixture.

    The synthetic version above proves the mechanism is wired. This one proves
    it is wired **to the thing that would actually regress**: the real corpus,
    the real `ms:lens-4-sample-optics`, and the oracle a person actually
    approved. `expertise: 1.9` is the weight that profile's own header says its
    captured priors live under -- drop it and the entry falls out of the top
    slot, which is exactly the change an oracle exists to notice.

    Skipped when nothing has been promoted, and that is a real skip rather than
    a hidden pass: the assertion needs an oracle, and there is no honest
    substitute for one.
    """
    import dataclasses

    from librarian.index import load_profiles
    from librarian.record import read_records

    oracles = read_records(ORACLES)
    if not oracles:
        pytest.skip("no oracle has been promoted yet; F9 has nothing to break")

    profiles = load_profiles(ROOT / "profiles")
    idx = _real_index(ms, tmp_path)
    try:
        for oracle in oracles:
            assert run(idx, oracle, profiles).ok, "a committed oracle regressed"

        lens4 = profiles.get("ms:lens-4-sample-optics")
        mine = [o for o in oracles
                if o["caller_profile"] == "ms:lens-4-sample-optics"]
        if not (lens4 and mine):
            pytest.skip("no lens-4 oracle to break")

        assert lens4.kind_weight.get("expertise", 1.0) > 1.0, (
            "this test breaks the profile by lowering `expertise`, which "
            "assumes it is raised in the first place")
        broken = dataclasses.replace(
            lens4, kind_weight={**lens4.kind_weight, "expertise": 0.5})
        results = [run(idx, o, {lens4.id: broken}) for o in mine]
        assert any(not r.ok for r in results), (
            "F9 FAILED on the real corpus: lowering the weight that profile "
            "exists to raise changed nothing the oracle could see.")
    finally:
        idx.close()


@pytest.mark.integration
def test_every_committed_oracle_still_passes(ms, tmp_path):
    """The regression suite itself, over whatever has actually been promoted.

    This is the payoff of the whole folder: `BUILD.md` §4-B's *"a profile
    actually changes results"* checked by accumulated real use rather than by
    nine fixtures. It grows on its own -- every promotion adds an assertion
    here without anyone editing this file.

    **A skip when the folder is empty, not a pass.** A vacuous green is BD's
    `tools/kb.py` reporting *"run-less knowledge 0"* for 126 entries, which is
    the failure this whole fixture is named after.
    """
    from librarian.index import load_profiles
    from librarian.record import read_records

    if not read_records(ORACLES):
        pytest.skip("no oracles promoted yet; nothing to regress against")
    idx = _real_index(ms, tmp_path)
    try:
        results = run_all(idx, ORACLES, load_profiles(ROOT / "profiles"))
    finally:
        idx.close()
    assert results, "read_records found oracles and run_all returned none"
    failed = [str(r) for r in results if not r.ok]
    assert failed == [], "\n".join(failed)
