"""One retrieval session: what was asked, and which hits were actually cited.

[../FEEDBACK.md](../FEEDBACK.md) is the design. The substitution it rests on:

    what can be stored is not "it was good" but "which hits were cited."
    The first is a judgment; the second is a fact.

So this module records a fact and refuses several things that look like one.
Every refusal below is a rule from that document made executable, because a
schema stated in prose and unenforced is how `kb/08-retrieval/` would become the
one folder in this repository that violates *prose is not state*.

**Three fields are derived here rather than accepted from the caller**, for the
reason `advances` is a property on `Doc` and not a column: a stored copy can
disagree with its source, and the disagreement is invisible afterwards.

  `index_sha`   the state the record was written against. Accepted from the
                caller it could name an index state that never existed, and
                promotion turns on **two distinct** SHAs (FEEDBACK §5)
  `index_stale` read off the same index, for the same reason
  `id`          the filename's digest, which decision 36 already computes over
                the record. Stored inside it, identity would be hashed twice
                and the two could disagree

**Nothing here promotes anything.** `sessions/ -> oracles/` is human-approved,
and that gate is the only damping on `C-001`'s loop: what ranks high gets
cited, having been cited it becomes an oracle, and being an oracle keeps it
ranked high. `promotion_status` reports how far a session is from qualifying and
stops there.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from librarian.record import Written, read_records, write_record

SCHEMA = "librarian.retrieval/0.1"

#: The verdict vocabulary, from FEEDBACK.md §2. Separated by **cause**, because
#: the fix differs by cause: `wrong_ranking` is fixed in `profiles/` and
#: `missing_entry` in `kb/`, and a scalar score renders both as one number.
VERDICTS = {
    "useful": "the cited hit was near the top",
    "wrong_ranking": "it was there, but low -- the fix is in profiles/",
    "missing_entry": "not in the corpus -- the fix is in kb/",
    "wrong_tier": "returned with the wrong tier -- the fix is the frontmatter",
    "no_result": "the search returned nothing -- tokenizer or adapter",
}

#: `not_searched` is in FEEDBACK.md's table and is deliberately **not** here.
#: It is the default of an *unrecorded* query -- "this was never checked" --
#: and a call to this tool is a record that someone did look. Accepting it
#: would let a caller file the absence of a record as a record, which is the
#: one distinction constraint ① exists to keep.
NOT_A_VERDICT = "not_searched"

ACTIONS = {"none", "challenge_raised", "entry_written", "profile_changed"}

#: A role, never a person -- decision 29, and rt T-018/T-035 (citations stay,
#: attributions go). Checked **here** and not only in `librarian.publish`,
#: because that gate short-circuits on a local-only folder: a session is never
#: committed, so the gate has nothing to say about it. A name in a session
#: would instead have to be stripped at promotion, by whoever approves it.
_ROLE = re.compile(r"^(agent|human:[a-z0-9][a-z0-9-]*)$")

_UID = re.compile(r"^[a-z]+:[^#]+#.+$")


class FeedbackError(ValueError):
    """A session this module will not write, with the rule that refused it."""


def _uids(name: str, value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise FeedbackError(f"{name} must be a list of uids, not {type(value).__name__}")
    out = []
    for v in value:
        s = str(v)
        if not _UID.match(s):
            raise FeedbackError(
                f"{name} contains {s!r}, which is not a uid. The form is "
                f"`repo:path#locator`, as `kb_search` returns it -- a record "
                f"that cannot be walked back to a location is not usable")
        out.append(s)
    return out


def session(query: str, caller_profile: str, verdict: str,
            returned: Any = None, cited: Any = None, missing: Any = None,
            asked_by: str = "agent", action: str = "none",
            action_ref: Optional[str] = None, note: Optional[str] = None,
            *, index_sha: dict[str, str], index_stale: bool,
            known_uids: Optional[set[str]] = None,
            known_profiles: Optional[set[str]] = None) -> dict[str, Any]:
    """The record, validated. Raises `FeedbackError` rather than storing a lie."""
    if not query.strip():
        raise FeedbackError(
            "query is empty, and it is the reproduction input: without it an "
            "oracle cannot be re-run (FEEDBACK decision 3)")

    if verdict == NOT_A_VERDICT:
        raise FeedbackError(
            f"{NOT_A_VERDICT!r} is the default of a query nobody recorded -- "
            f"'this was never checked'. Calling this tool *is* the record that "
            f"someone looked, so it cannot be the verdict. Use `no_result` if "
            f"the search returned nothing.")
    if verdict not in VERDICTS:
        raise FeedbackError(
            f"verdict {verdict!r} is not one of {sorted(VERDICTS)}. The "
            f"vocabulary separates causes because the fix differs by cause")
    if action not in ACTIONS:
        raise FeedbackError(f"action {action!r} is not one of {sorted(ACTIONS)}")

    if not _ROLE.match(asked_by):
        raise FeedbackError(
            f"asked_by={asked_by!r} is not a role. It is `agent` or a `human:*` "
            f"profile and never a name: this repository is public, and a "
            f"person-keyed record says who was looking for what "
            f"(decision 29, rt T-018)")

    if known_profiles is not None and caller_profile not in known_profiles:
        raise FeedbackError(
            f"caller_profile {caller_profile!r} is not a stored profile. A "
            f"session names the profile the search actually ran under, and one "
            f"that does not exist cannot be reproduced")

    ret = _uids("returned", returned)
    cit = _uids("cited", cited)
    mis = _uids("missing", missing)

    extra = [u for u in cit if u not in set(ret)]
    if extra:
        raise FeedbackError(
            f"cited contains {extra[0]!r}, which is not in `returned`. A "
            f"citation is of something this search returned; what was needed "
            f"and not returned belongs in `missing`")

    # `returned` and `cited` came out of a search, so they have to resolve.
    # `missing` deliberately does not: its whole point is a uid the corpus does
    # not hold, which is what `missing_entry` means.
    if known_uids is not None:
        absent = [u for u in ret if u not in known_uids]
        if absent:
            raise FeedbackError(
                f"returned contains {absent[0]!r}, which is not in the index. "
                f"An oracle built on it could never pass, so it is refused now "
                f"rather than at promotion")

    if verdict == "useful" and not cit:
        raise FeedbackError(
            "verdict `useful` means the cited hit was near the top, and `cited` "
            "is empty. A session with no citation carries no signal "
            "(FEEDBACK §5)")
    if verdict == "no_result" and ret:
        raise FeedbackError(
            "verdict `no_result` says the search returned nothing, and "
            "`returned` is not empty")

    rec = {
        "schema": SCHEMA,
        "query": query,
        "caller_profile": caller_profile,
        "asked_by": asked_by,
        "index_sha": dict(sorted(index_sha.items())),
        "index_stale": bool(index_stale),
        "returned": ret,
        "cited": cit,
        "missing": mis,
        "verdict": verdict,
        "action": action,
        "action_ref": str(action_ref) if action_ref else None,
    }
    # `note` is prose and **no code branches on it** (FEEDBACK §4②). It is
    # omitted entirely when absent rather than stored as null, so a reader
    # cannot mistake an empty note for a considered one.
    if note:
        rec["note"] = note
    return rec


def record_id(written: Written) -> str:
    """`ret-<digest>`. Derived from the file, never stored inside it."""
    return f"ret-{written.digest}"


def write(directory: Path, rec: dict[str, Any], date: str) -> Written:
    """Append one session. Idempotent: a retried report is one record.

    That matters more than it looks. Promotion requires the same session under
    **two distinct `index_sha`** (FEEDBACK §5), a condition put there to stop an
    agent promoting its own retrieval results. A retry landing twice would let
    one caller satisfy it without a second index state ever existing.
    """
    return write_record(directory, rec, date, rec["caller_profile"])


def promotion_status(directory: Path, query: str,
                     caller_profile: str) -> dict[str, Any]:
    """How far this query is from qualifying as an oracle -- and no further.

    Reported so the caller need not guess, and so the human approving a
    promotion can see the condition already met rather than recompute it. The
    approval itself is not here and is not automatable: it is the only damping
    on the loop, and it is also the disclosure review that lets `oracles/` be
    committed at all (PLAN.md §6.1, decision 37).
    """
    shas: set[str] = set()
    sessions = 0
    for rec in read_records(directory):
        if rec.get("query") != query or rec.get("caller_profile") != caller_profile:
            continue
        sessions += 1
        if rec.get("verdict") == "useful" and rec.get("cited"):
            shas.add(repr(sorted(rec.get("index_sha", {}).items())))

    awaiting = []
    if not shas:
        awaiting.append("a session with verdict `useful` and a non-empty `cited`")
    elif len(shas) < 2:
        awaiting.append("the same result under a second, distinct index_sha")
    awaiting.append("human approval, which is not automatable")
    return {
        "sessions": sessions,
        "qualifying_index_states": len(shas),
        "reproductions_required": 2,
        "awaiting": awaiting,
        "promoted": False,
    }
