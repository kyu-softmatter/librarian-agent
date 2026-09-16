"""The publish gate, and the `.gitignore` that has to agree with it.

PLAN.md §6.1 · FEEDBACK.md open (a). This repository is public, and rt `T-019`①
is why the gate is a Phase 0 item rather than a later one: *"in a public repo,
deleting the file afterwards does not undo the disclosure."*

**Two halves, and a rule that only names one of them decays.** `librarian/publish.py`
says which folders are committed; `.gitignore` is what actually enforces it.
These tests assert the two agree, because a disclosure rule written in a
docstring and contradicted by a config file is worse than neither -- it reads as
a guarantee.
"""

import json
import subprocess
from pathlib import Path

import pytest

from librarian.publish import (IN_GIT, LOCAL_ONLY, MAY_CARRY_QUERY, gate,
                              is_local_only)

ROOT = Path(__file__).resolve().parent.parent


def _git(*args: str) -> str:
    return subprocess.run(("git", *args), cwd=ROOT, capture_output=True,
                          text=True).stdout


def _ignored(rel: str) -> bool:
    return subprocess.run(("git", "check-ignore", "-q", rel), cwd=ROOT).returncode == 0


# --- the two halves agree ---------------------------------------------------

def test_every_local_only_folder_is_actually_git_ignored():
    """The half that is non-vacuous today, before any record exists.

    A folder declared local-only and not ignored is the whole failure: the first
    session written lands in `git status` looking like something to commit.
    """
    for folder in LOCAL_ONLY:
        probe = f"{folder}probe.json"
        assert _ignored(probe), (
            f"{folder} is declared local-only in librarian/publish.py and "
            f"`git check-ignore` does not ignore it")


def test_no_committed_folder_is_git_ignored():
    """The mirror, and it catches a `.gitignore` pattern that is too broad.

    `kb/08-retrieval/sessions/*` and `kb/08-retrieval/*` are one character
    apart, and the second silently stops committing oracles -- which would be
    discovered as *"the regression oracles never ran in CI"*, long after.
    """
    for folder in IN_GIT:
        probe = f"{folder}probe.json"
        assert not _ignored(probe), (
            f"{folder} is declared committed in librarian/publish.py and "
            f"`.gitignore` ignores it")


def test_the_gitkeep_files_are_tracked_so_the_folders_survive():
    tracked = set(_git("ls-files").split())
    for folder in LOCAL_ONLY + IN_GIT:
        keep = f"{folder}.gitkeep"
        assert keep in tracked, f"{keep} is not tracked; the folder vanishes"


# --- the gate itself --------------------------------------------------------

SESSION = {
    "schema": "librarian.retrieval/0.1",
    "query": "bleach photons for AlexaFluor488 at 470 nm",
    "caller_profile": "ms:lens-5-photo-perturbation",
    "asked_by": "agent",
    "cited": ["ms:data/fluorophores.yaml#AlexaFluor488"],
    "verdict": "useful",
}


def test_a_session_is_local_only_so_the_gate_has_nothing_to_say():
    assert is_local_only("kb/08-retrieval/sessions/x.json")
    assert gate("kb/08-retrieval/sessions/x.json", SESSION) == []


def test_raw_query_text_passes_only_in_oracles():
    """The one exception, and the reason it is not a hole.

    An oracle *is* `(query, caller_profile) -> cited` and cannot be re-run
    without the text (FEEDBACK decision 3) -- hashing it, which is option 1 of
    open (a), removes the only grader retrieval has. The protection is not that
    the text is absent but that **a person read it before it was committed**:
    promotion is human-approved already, for anti-self-confirmation reasons,
    and that approval is the disclosure review.
    """
    assert MAY_CARRY_QUERY == ("kb/08-retrieval/oracles/",)
    assert gate("kb/08-retrieval/oracles/x.json", SESSION) == []

    codes = [f.check for f in gate("kb/08-retrieval/findings/x.json", SESSION)]
    assert codes == ["publish_raw_query"], codes


def test_a_finding_names_the_cause_and_not_the_query():
    """`kb/08-retrieval/findings/` is *"why a profile fails -- the cause, not
    the symptom."* A quoted query is the symptom, and it is also the disclosure."""
    ok = {"schema": "librarian.finding/0.1", "cause": "wrong_ranking",
          "profile": "ms:lens-5-photo-perturbation",
          "note": "kind_weight put doc_section above the registry field"}
    assert gate("kb/08-retrieval/findings/x.json", ok) == []


def test_a_record_that_names_a_person_is_refused():
    """rt T-018 · T-035: citations stay, attributions go."""
    for key in ("author", "email", "operator", "reviewer"):
        rec = {**{k: v for k, v in SESSION.items() if k != "query"}, key: "KH"}
        codes = [f.check for f in gate("store/challenge/x.json", rec)]
        assert "publish_names_a_person" in codes, key


def test_asked_by_is_a_role_and_never_a_name():
    base = {k: v for k, v in SESSION.items() if k != "query"}
    for role in ("agent", "human:instrument-operator", "human:reader"):
        assert gate("store/challenge/x.json", {**base, "asked_by": role}) == [], role
    for name in ("KH", "kyuhwan", "Kyu Choi", "human:"):
        codes = [f.check for f in
                 gate("store/challenge/x.json", {**base, "asked_by": name})]
        assert "publish_asked_by_is_not_a_role" in codes, name


def test_an_undeclared_folder_is_an_error_rather_than_a_default():
    """Neither committed nor ignored by rule is the state the gate removes.

    The same shape as `not_searched` against `searched_empty`: an absent
    decision has to be visible, not resolved into whichever branch is easier.
    """
    codes = [f.check for f in gate("store/somewhere-new/x.json", {"a": 1})]
    assert "publish_folder_undeclared" in codes


# --- over what is actually committed ---------------------------------------

def test_every_committed_record_passes_its_own_gate():
    """Vacuous until the first record lands, and load-bearing from then on.

    Kept because the alternative is checking it by hand at review time, which
    is exactly how BD's `INDEX.md` came to state 40 entries for 42 files.
    """
    tracked = [p for p in _git("ls-files").split()
               if p.startswith(IN_GIT) and p.endswith(".json")]
    failures = []
    for rel in tracked:
        try:
            rec = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            failures.append(f"{rel}: not JSON ({e})")
            continue
        if isinstance(rec, dict):
            failures += [f"{rel}: {f.check} -- {f.detail}" for f in gate(rel, rec)]
    assert failures == [], failures[:5]


def test_no_tracked_file_under_sessions_exists_at_all():
    """The gate's one absolute. A session that reached git cannot be unpublished."""
    tracked = [p for p in _git("ls-files").split()
               if p.startswith("kb/08-retrieval/sessions/")
               and not p.endswith(".gitkeep")]
    assert tracked == [], tracked
