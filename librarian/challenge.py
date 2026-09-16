"""One challenge: doubt against a claim, with the work order that would settle it.

The schema is **research-topic's**, `design/kb-schema.md` §4.7, and it is theirs
rather than ours on purpose -- a challenge is the one entry kind written from
any side, including BD or MS writing one against an entry held here
(`charter.md` §3: *"ownership is fixed; the direction of a work order is
not"*). So the field names and vocabularies below are quoted, not designed.

**`falsifier_cited` is what makes this a work order rather than an argument**
(`T-048`). It is mandatory and it must point **into the target**, not into the
challenger, which is checkable here and is checked: a citation that lands
outside the target's own file is the prohibited move -- a challenge may not
cite a new basis, because that puts a mass of counter-argument back in the slot
`personas/_common.md` §3 was vacated to empty (`C-005`).

Two consequences look like bugs and are not:

  an entry with no falsifier cannot be challenged -- a defect in the **entry**,
  since every judgment is supposed to carry the check that would overturn it,
  and not a limitation here

  routing is decided by the falsifier's **type** and never by the sender, so
  `raised_by` is recorded and nothing reads it

**What this repository settles, and it is one thing.** For
`resolvable_by: literature`, whether the cited locator exists. Everything else
returns `unknown`. rt records the literature route as `C-007`, *"the largest
unclosed item in this document"* -- two of three routes resolve on code
producing a number and the third resolves on someone reading a paper, which is
what `I-052` forbids of a gate. rt considered the presence-of-a-locator escape
and did **not** adopt it; this repository does, deliberately, because it is
deterministic and it answers a weaker question than the challenge asked.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from librarian.record import Written, read_records, write_record

SCHEMA = "rt.challenge/0.1"

#: `doubt_kind` -> (`resolvable_by`, `routed_to`). **This table is the router**
#: (`kb-schema.md` §4.7: *"the gate, from `doubt_kind` -> `resolvable_by` ->
#: `routed_to`"*), and it takes no other input. Not the sender, not the target's
#: repo, and not what the answer would turn out to be.
ROUTES: dict[str, tuple[str, str]] = {
    # the published number does not transfer to this setup -> a local measurement
    "superseded_by_measurement": ("ms_experiment", "ms"),
    # the claim is contradicted by what the model does -> a run
    "contradicted_by_run": ("bd_run", "bd"),
    # the conditions of validity were never checked -> literature
    "conditions_not_met": ("literature", "research-topic"),
    # used outside the scope it stated -> no falsifier available
    "scope_exceeded": ("not_resolvable", "human"),
    # **`never_verified` names no resolver, so it gets none.** The other four
    # doubt kinds each say what would settle them; this one says only that
    # nothing has. Picking a route for it would be a guess about which
    # instrument or model applies, and routing by guess is the failure the
    # "never by the sender" rule exists to prevent. A person re-raises it with
    # a doubt kind that names a falsifier.
    "never_verified": ("not_resolvable", "human"),
}

DOUBT_KINDS = tuple(ROUTES)

#: rt's `state` vocabulary, verbatim. `not_run` is **not** in it -- this
#: repository's `store/README.md` said it was, and that was drift between the
#: two documents rather than a third state.
STATES = ("raised", "routed", "declined", "running", "upheld", "rejected",
          "unknown")

#: Beyond this, a challenge goes to a person regardless of its doubt kind.
#:
#: **Declared here, and narrower than rt has specified.** `Q-010` records that
#: *"a challenge has no cost ceiling and no declined-forever state"* and leaves
#: both open, while `T-049` requires the bound to exist at all: without it the
#: loop circulates doubt instead of topics, which is `C-001` in a new costume.
#: So this is a bound chosen to be finite rather than to be correct -- a third
#: round of doubt on one claim is the point at which the thing being tested is
#: the loop and not the claim. It escalates rather than refuses, because a
#: refusal loses the challenge and escalation keeps it.
MAX_AUTOMATIC_DEPTH = 2

_COST_FIELDS = ("gpu_hours", "instrument_hours", "search_budget_spent")

_UID = re.compile(r"^([a-z]+):([^#]+)#(.+)$")


class ChallengeError(ValueError):
    """A challenge this module will not write, with the rule that refused it."""


def _split(uid: str, name: str) -> tuple[str, str, str]:
    m = _UID.match(uid)
    if not m:
        raise ChallengeError(
            f"{name}={uid!r} is not a uid. The form is `repo:path#locator`, as "
            f"`kb_search` returns it")
    return m.group(1), m.group(2), m.group(3)


def _profile_repo(caller_profile: str) -> str:
    """`ms:lens-5-...` -> `ms`. Derived so `raised_by` cannot disagree with the
    profile the call was actually made under -- and it is recorded rather than
    read, because routing by the sender is the thing forbidden."""
    return caller_profile.split(":", 1)[0] if ":" in caller_profile else caller_profile


def challenge(target_uid: str, doubt_kind: str, falsifier_cited: str,
              caller_profile: str, note: Optional[str] = None,
              cost: Optional[dict[str, float]] = None,
              in_reply_to: Optional[str] = None,
              *, target: Optional[dict[str, Any]] = None,
              falsifier_exists: bool = True,
              prior_depth: Optional[int] = None) -> dict[str, Any]:
    """The record, validated and routed. Raises `ChallengeError` instead of
    writing a challenge nobody could act on."""
    t_repo, t_path, t_locator = _split(target_uid, "target_uid")
    f_repo, f_path, _ = _split(falsifier_cited, "falsifier_cited")

    if doubt_kind not in ROUTES:
        raise ChallengeError(
            f"doubt_kind {doubt_kind!r} is not one of {sorted(ROUTES)}. The "
            f"doubt kind is what routes the challenge, so it cannot be free text")

    if (f_repo, f_path) != (t_repo, t_path):
        raise ChallengeError(
            f"falsifier_cited points at {f_repo}:{f_path}, which is not the "
            f"target's own file ({t_repo}:{t_path}). A challenge cites the "
            f"target's own falsification condition -- citing a new basis is the "
            f"prohibited move (T-048), and it turns a work order back into an "
            f"argument")

    if target is None:
        raise ChallengeError(
            f"target {target_uid!r} is not in the index. A challenge against a "
            f"claim nobody can open is not actionable")

    if not falsifier_exists:
        raise ChallengeError(
            f"falsifier_cited {falsifier_cited!r} does not resolve. The usual "
            f"cause is an edited heading -- `kb_get` on the target's path lists "
            f"the locators it actually has")

    if not target.get("has_falsifier"):
        raise ChallengeError(
            f"{target_uid} carries no falsification condition, so it cannot be "
            f"challenged. **That is a defect in the entry** -- every judgment is "
            f"supposed to carry the check that would overturn it -- and not a "
            f"limitation here. `kb_stale` reports it as an entry defect; the fix "
            f"is to give the entry a falsifier, which is a pull request against "
            f"{t_repo}")

    depth = 0 if in_reply_to is None else (prior_depth or 0) + 1
    resolvable_by, routed_to = ROUTES[doubt_kind]
    escalated = depth > MAX_AUTOMATIC_DEPTH
    if escalated:
        # Depth is the signal that doubt is circulating rather than resolving,
        # and the answer to that is a person -- the same damping device as the
        # `not_resolvable` route (T-034).
        resolvable_by, routed_to = "not_resolvable", "human"

    rec = {
        "schema": SCHEMA,
        "target": {"repo": t_repo, "entry": t_path, "claim": t_locator},
        "target_uid": target_uid,
        "raised_by": _profile_repo(caller_profile),
        "caller_profile": caller_profile,
        "doubt_kind": doubt_kind,
        "falsifier_cited": falsifier_cited,
        "resolvable_by": resolvable_by,
        "routed_to": routed_to,
        # `raised` is unreachable through this tool: routing is a lookup that
        # completes before the record exists, so there is no moment at which a
        # challenge here has a target and no route. One fewer state to go stale.
        "state": "routed",
        "resolved_by": None,
        "depth": depth,
        "in_reply_to": in_reply_to,
        "cost": {f: float((cost or {}).get(f, 0) or 0) for f in _COST_FIELDS},
    }
    if escalated:
        rec["escalated_at_depth"] = MAX_AUTOMATIC_DEPTH
    if note:
        rec["note"] = note
    return rec


def record_id(written: Written) -> str:
    """`chal-<digest>`, derived from the filename.

    **rt's schema illustrates `chal-0001`, and the substitution is not a
    deviation -- it is PLAN.md Phase 2's ID-issuance row**, which answers
    `kb-schema.md` §6's own open question (*"who issues entry IDs -- sequential
    numbers collide under parallel writes"*) with a content hash, inheriting
    BD's `run_id` approach. Decision 36 then makes the filename that hash, so
    the id is read off the file rather than stored twice inside it.

    A counter would also be the one shape decision 36 has no answer for: a
    rollup two writers contend over.
    """
    return f"chal-{written.digest}"


def write(directory: Path, rec: dict[str, Any], date: str) -> Written:
    return write_record(directory, rec, date, rec["doubt_kind"])


def depth_of(directory: Path, challenge_id: str) -> Optional[int]:
    """The depth of an existing challenge, by its `chal-<digest>` id."""
    want = challenge_id.removeprefix("chal-")
    for p in sorted(directory.glob("*.json")):
        if p.stem.endswith(f"-{want}"):
            import json
            return int(json.loads(p.read_text(encoding="utf-8")).get("depth", 0))
    return None


def open_against(directory: Path, target_uid: str) -> list[dict[str, Any]]:
    """Challenges already standing against this claim.

    Reported so a caller can see that the doubt is already filed rather than
    raise it again under a different wording -- two records for one work order
    is how a queue of work becomes a queue of opinions.
    """
    return [r for r in read_records(directory)
            if r.get("target_uid") == target_uid
            and r.get("state") not in ("upheld", "rejected", "declined")]
