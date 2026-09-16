"""The publish gate: which records this public repository may commit.

`PLAN.md` §6.1 and `FEEDBACK.md` open (a). The exposure path is
`kb/08-retrieval/`, which stores query text, and the reason it outranks the
digest is rt `T-019`①:

    "in a public repo, deleting the file afterwards does not undo the
     disclosure."

**The rule is folder-level, and that is inherited rather than chosen.** BD
solved the same problem by putting `source/papers/` in git and gitignoring
`source/lab/`, *"because what has to be protected is not the author but the fact
that it is not yet published."* So the question is never asked per record at
commit time; it is answered by which directory the record is in.

| Folder | In git | Why |
|---|---|---|
| `kb/08-retrieval/sessions/` | **no** | Accumulates automatically. No human reads a session before it lands, and volume guarantees none ever will |
| `kb/08-retrieval/oracles/` | yes | A promotion is **human-approved** already (`FEEDBACK.md` §5), and that approval is the disclosure review |
| `kb/08-retrieval/findings/` | yes | A finding names *the cause* -- a weight, a tokenizer limit, a missing entry. A quoted query is the symptom |
| `store/challenge/` | yes | A challenge cites a locator in a public repository. It carries no query |

**The one thing that is not folder-level is `query`, and it is allowed in
exactly one place.** An oracle *is* `(query, caller_profile) -> cited`, so it
cannot exist without the raw text -- `FEEDBACK.md` decision 3 keeps it for that
reason, and hashing it (option 1 of open (a)) would make an oracle unrunnable,
which removes the only grader retrieval has (§3). The protection is not that the
text is absent; it is that **a person read it before it was committed.**

The cost, stated rather than discovered later: a query that reveals a direction
**cannot be promoted**. It stays a session -- still a usable regression check for
whoever holds it locally, and one CI will never run.

**And no record here names a person.** rt `T-018` · `T-035`: citations stay,
attributions go. `asked_by` is a role (`agent`, or a `human:*` profile), never a
name -- the same rule as decision 29, for the same reason: a person-keyed record
in a public repository records who was looking for what.
"""

from __future__ import annotations

import re
from typing import Any

from librarian.doc import Finding

#: Directories whose records are committed. Anything not listed is local-only,
#: and the `.gitignore` is what enforces that -- this table is what lets a
#: writer know before it writes, and what `tests/test_publish_gate.py` checks
#: the `.gitignore` against, so the two cannot drift.
IN_GIT = (
    "kb/08-retrieval/oracles/",
    "kb/08-retrieval/findings/",
    "store/challenge/",
    "store/crosswalk/",
    "store/digest/",
    "store/inbox/",
)

LOCAL_ONLY = (
    "kb/08-retrieval/sessions/",
)

#: The one folder whose records may carry raw query text, because an oracle is
#: defined as `(query, caller_profile) -> cited` and cannot be re-run without it.
MAY_CARRY_QUERY = ("kb/08-retrieval/oracles/",)

#: A role, never a person (decision 29).
_ROLE = re.compile(r"^(agent|human:[a-z0-9][a-z0-9-]*)$")

#: Keys that name a person rather than a role. Not a guess at every possible
#: spelling -- it is the set this repository's own schemas could plausibly grow,
#: and a key nobody thought of is caught by `_ROLE` on `asked_by` instead.
_PERSON_KEYS = frozenset({
    "author", "authors", "user", "username", "email", "operator", "person",
    "asked_by_person", "requested_by", "owner_name", "reviewer",
})


def is_local_only(rel_path: str) -> bool:
    return rel_path.startswith(LOCAL_ONLY)


def gate(rel_path: str, record: dict[str, Any]) -> list[Finding]:
    """What would be wrong with committing this record at this path.

    An empty list is a pass. A record under `LOCAL_ONLY` always passes: it is
    not going to be committed, so the gate has nothing to say about it -- the
    `.gitignore` is what keeps that true, and a test asserts the two agree.
    """
    if is_local_only(rel_path):
        return []
    out: list[Finding] = []

    if not rel_path.startswith(IN_GIT):
        out.append(Finding(
            "publish_folder_undeclared", rel_path,
            "no publish-gate rule covers this folder. A record whose folder is "
            "not declared is neither committed nor ignored by rule, which is "
            "the state the gate exists to remove", "error"))

    if "query" in record and not rel_path.startswith(MAY_CARRY_QUERY):
        out.append(Finding(
            "publish_raw_query", rel_path,
            "carries raw query text outside oracles/. What someone was looking "
            "for is what they are about to do, and deleting the file afterwards "
            "does not undo the disclosure (rt T-019)", "error"))

    for key in sorted(_PERSON_KEYS & record.keys()):
        out.append(Finding(
            "publish_names_a_person", f"{rel_path}#{key}",
            f"{key!r} names a person. Citations stay and attributions go "
            f"(rt T-018, T-035); a role belongs in `asked_by`", "error"))

    asked = record.get("asked_by")
    if asked is not None and not _ROLE.match(str(asked)):
        out.append(Finding(
            "publish_asked_by_is_not_a_role", f"{rel_path}#asked_by",
            f"asked_by={asked!r} is not a role. Profiles multiply with kinds of "
            f"question, not with people (decision 29)", "error"))
    return out
