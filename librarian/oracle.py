"""A past confirmed citation, re-run as a regression test.

Retrieval has no grader. BD hit the same wall and answered it the same way --
`knowledge/wiki/CLAUDE.md`: *"our domain has no grader, so the literature
stands in for one."* Here **a citation someone actually made stands in for
one**, which is why `cited` is the field `kb_feedback` exists to collect.

That turns `BUILD.md` §4-B's *"a profile actually changes results"* from a claim
checked by nine fixtures into one checked by accumulated real use.

**Fixture F9 is the acceptance condition, and its pass condition is that
something fails**: create one oracle, break the profile on purpose, and the
test must go red. Stay green and the oracle is an unwired checker -- BD's
`tools/kb.py`, which reported *"run-less knowledge 0"* for 126 existing entries
because its path had been renamed. `tests/test_oracle.py` is that fixture.

**`within_top` is measured, not chosen.** It is the worst rank the citation
actually achieved across the sessions being promoted. Chosen, it would be
either so loose that no regression trips it or so tight that ordinary reranking
does -- and neither failure says anything about retrieval.

**Nothing here promotes.** `promote()` refuses unless every condition in
`FEEDBACK.md` §5 is met, and the last of them is a human, who is not a
function: an agent promoting its own retrieval results to ground truth is a
self-confirming loop -- what ranks high gets cited, having been cited it becomes
an oracle, being an oracle keeps it ranked high. The `librarian promote`
command is where a person supplies that condition, and the commit that follows
records who did.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from librarian.record import Written, read_records, write_record

SCHEMA = "librarian.oracle/0.1"


class PromotionError(ValueError):
    """A promotion this module refuses, with the condition that was not met."""


@dataclass(frozen=True)
class OracleResult:
    """One oracle, run. `ranks` is what it actually saw, so a failure report
    says *how far* it slipped rather than only that it did."""
    query: str
    caller_profile: str
    within_top: int
    ranks: dict[str, Optional[int]]

    @property
    def missing(self) -> list[str]:
        return sorted(u for u, r in self.ranks.items()
                      if r is None or r > self.within_top)

    @property
    def ok(self) -> bool:
        return not self.missing

    def __str__(self) -> str:
        state = "ok" if self.ok else "REGRESSED"
        shown = ", ".join(f"{u}@{r if r else '-'}" for u, r in self.ranks.items())
        return (f"[{state}] {self.caller_profile} :: {self.query!r} "
                f"within_top={self.within_top}  {shown}")


def rank_of(index, query: str, profile, uids: list[str],
            limit: int) -> dict[str, Optional[int]]:
    """Where each uid lands, searched exactly as a caller would.

    The same `limit` and the same per-path diversification, deliberately: an
    oracle that measured something callers do not see would pass while the
    answer they get gets worse.
    """
    hits = index.search(query, profile, limit=limit).hits
    order = {h.uid: i + 1 for i, h in enumerate(hits)}
    return {u: order.get(u) for u in uids}


def run(index, oracle: dict[str, Any], profiles: dict[str, Any]) -> OracleResult:
    prof = profiles.get(oracle["caller_profile"])
    if prof is None:
        raise PromotionError(
            f"oracle names profile {oracle['caller_profile']!r}, which is not "
            f"loaded. An oracle over a deleted profile tests nothing, and a "
            f"skipped oracle is the unwired checker F9 exists to catch")
    within = int(oracle["within_top"])
    return OracleResult(
        query=oracle["query"], caller_profile=oracle["caller_profile"],
        within_top=within,
        ranks=rank_of(index, oracle["query"], prof, list(oracle["cited"]),
                      limit=within))


def run_all(index, directory: Path,
            profiles: dict[str, Any]) -> list[OracleResult]:
    return [run(index, o, profiles) for o in read_records(directory)]


def _sha_key(rec: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    """An index state, hashable so two sessions can be counted as one or two.

    A tuple and **not** its `repr`: the first version keyed on the repr, which
    was fine for the set and then leaked into the committed oracle as
    `"[('bd', 'a18e171'), ('ms', '196cdf1')]"` -- a Python literal inside JSON,
    in a file whose whole purpose is to be read by something else later.
    """
    return tuple(sorted((rec.get("index_sha") or {}).items()))


def build_oracle(sessions: list[dict[str, Any]], index, profiles,
                 headroom: int = 0) -> dict[str, Any]:
    """The oracle a set of sessions supports -- and only what they support.

    Every session has to agree on the query, the profile and the citation:
    promotion is of *one* confirmed result, and averaging two different ones is
    how a scalar score gets in through the side door.
    """
    if not sessions:
        raise PromotionError("no sessions to promote")
    queries = {s["query"] for s in sessions}
    profs = {s["caller_profile"] for s in sessions}
    if len(queries) != 1 or len(profs) != 1:
        raise PromotionError(
            f"sessions disagree: {len(queries)} queries, {len(profs)} profiles. "
            f"An oracle is one confirmed result, not a summary of several")

    query, profile = queries.pop(), profs.pop()
    cited = sorted({u for s in sessions for u in s.get("cited", [])})
    if not cited:
        raise PromotionError("nothing was cited, so there is nothing to assert")

    prof = profiles.get(profile)
    if prof is None:
        raise PromotionError(f"profile {profile!r} is not loaded")

    # The worst rank actually observed, measured now against the live index.
    # `limit` is generous here because this is the measurement, not the
    # assertion -- the assertion is `within_top`, which comes out of it.
    ranks = rank_of(index, query, prof, cited, limit=50)
    unranked = [u for u, r in ranks.items() if r is None]
    if unranked:
        raise PromotionError(
            f"{unranked[0]} is not returned for this query under {profile} at "
            f"all, so an oracle asserting it would fail the moment it was "
            f"written. Either the index moved or the session recorded a "
            f"citation the search cannot reproduce")

    within = max(ranks.values()) + headroom
    return {
        "schema": SCHEMA,
        "query": query,
        "caller_profile": profile,
        "cited": cited,
        # Measured, not chosen -- see the module docstring.
        "within_top": int(within),
        "observed_ranks": {u: int(r) for u, r in sorted(ranks.items())},
        # Each index state as an object, so a reader gets the SHAs rather
        # than a string to parse back.
        "reproduced_under": [dict(k) for k in sorted({_sha_key(s)
                                                      for s in sessions})],
        "promoted_from": sorted(s["_id"] for s in sessions if s.get("_id")),
    }


def check_promotable(sessions: list[dict[str, Any]]) -> list[str]:
    """Which of FEEDBACK §5's conditions these sessions do not meet.

    Human approval is not in the list, because it is not a property of the
    records. It is supplied by a person running `librarian promote`, and no
    return value from this function can stand in for it.
    """
    unmet = []
    qualifying = [s for s in sessions
                  if s.get("verdict") == "useful" and s.get("cited")]
    if not qualifying:
        unmet.append("a session with verdict `useful` and a non-empty `cited` "
                     "-- a failure record is not an oracle")
    if len({_sha_key(s) for s in qualifying}) < 2:
        unmet.append("the same result under two distinct index_sha -- one is "
                     "indistinguishable from chance")
    return unmet


def promote(oracles_dir: Path, sessions: list[dict[str, Any]], index, profiles,
            date: str, *, approved_by_a_person: bool,
            query_may_be_published: bool) -> Written:
    """Write the oracle. Both flags are a person's assertion, not a check.

    They are separate because they are different judgments about different
    things, and collapsing them would hide the second. **`approved_by_a_person`
    is the damping on the loop** (`C-001`). **`query_may_be_published` is the
    disclosure review** that lets `oracles/` be committed at all: `sessions/`
    is gitignored precisely because nobody reads a session before it lands, and
    promotion is the moment someone does (PLAN.md §6.1, decision 37).
    """
    unmet = check_promotable(sessions)
    if unmet:
        raise PromotionError("not promotable: " + "; ".join(unmet))
    if not approved_by_a_person:
        raise PromotionError(
            "promotion requires a person's approval and nothing here can "
            "supply it. An agent promoting its own retrieval results to ground "
            "truth is a self-confirming loop (FEEDBACK.md §5)")
    if not query_may_be_published:
        raise PromotionError(
            "an oracle carries its raw query and `oracles/` is committed to a "
            "public repository, so promoting one publishes the query. That is "
            "a separate judgment from whether the result is an oracle, and it "
            "has to be made (PLAN.md §6.1)")

    qualifying = [s for s in sessions
                  if s.get("verdict") == "useful" and s.get("cited")]
    oracle = build_oracle(qualifying, index, profiles)
    return write_record(oracles_dir, oracle, date, oracle["caller_profile"])
