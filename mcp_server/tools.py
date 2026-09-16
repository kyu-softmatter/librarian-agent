"""The seven read tools, over the index and nothing else.

Every tool opens the index per call rather than holding a handle. A reindex
deletes and rewrites the file, so a long-lived connection would answer from a
database that no longer exists -- silently, which is the failure mode this
project exists to catch.

Descriptions say what a result means, not only what a tool does. A model that
reads `searched_empty` as a tool failure will try to route around it, and
`agentic-microscope`'s own MCP server had to say the same thing about a refusal.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from mcp.types import ToolAnnotations

from librarian.index import Index, load_profiles

NO_INDEX = {
    "status": "no_index",
    "detail": "index/kb.sqlite is absent. Build it with "
              "`python -m librarian.cli reindex --repo ms`.",
}

EMPTY_NOTE = (
    "`status: searched_empty` is a result and not a tool failure: the corpus was "
    "searched and held nothing. It is distinct from `not_searched`, which is the "
    "absence of a record that anyone looked."
)

STALE_NOTE = (
    "`index_stale: true` means an indexed repository has moved since the index "
    "was built, so the answer may be behind. It is a warning on a valid answer, "
    "not an error."
)

LOCAL_ONLY_NOTE = (
    "A session is written to `kb/08-retrieval/sessions/`, which is gitignored "
    "permanently: it holds raw query text and this repository is public, and "
    "what someone was looking for is what they are about to do. `committed: "
    "false` is the policy, not a pending step."
)

PROMOTION_NOTE = (
    "`promotion_status` is a report and promotes nothing. An oracle needs the "
    "same result under two distinct index states and a human's approval -- an "
    "agent promoting its own retrieval results to ground truth is a "
    "self-confirming loop, and the approval is the only damping on it."
)

VERDICT_NOTE = (
    "useful | wrong_ranking (fix in profiles/) | missing_entry (fix in kb/) | "
    "wrong_tier (fix the entry's frontmatter) | no_result (tokenizer or "
    "adapter). `not_searched` is the default of an unrecorded query and is not "
    "accepted here."
)

DOUBT_KINDS_NOTE = (
    "superseded_by_measurement (-> ms) | contradicted_by_run (-> bd) | "
    "conditions_not_met (-> research-topic) | scope_exceeded (-> a human) | "
    "never_verified (-> a human, because it names no falsifier). The doubt kind "
    "is what routes the challenge, so it cannot be free text."
)

ROUTING_NOTE = (
    "`routed_to` is decided by the falsifier's type and by nothing else -- not "
    "by who raised it, and not by what the answer would turn out to be. "
    "`raised_by` is recorded and no code reads it."
)

LITERATURE_NOTE = (
    "On the `literature` route this server settles one thing only: whether the "
    "cited locator exists. The verdict stays `unknown`, because resolving it "
    "means someone reading the paper, which is not something a gate may do. "
    "rt records this as `C-007`, the largest unclosed item in its schema."
)

TIER_NOTE = (
    "Every hit carries `evidence` and `advances`. `advances: false` means that "
    "tier cannot advance a verdict -- a literature value never can, by rule. "
    "That is the state of the evidence, not a shortcoming of the result, and it "
    "should be reported rather than worked around."
)


def _today() -> str:
    """The day the record is about. Read once, at the call site, so nothing
    deeper in the write path depends on a clock (`librarian/record.py`)."""
    from datetime import date
    return date.today().isoformat()


def register(server, index_path: Path, profiles_dir: Path,
             cache_dir: Optional[Path] = None,
             sessions_dir: Optional[Path] = None,
             challenge_dir: Optional[Path] = None) -> None:
    read_only = ToolAnnotations(read_only_hint=True, destructive_hint=False)
    # `kb_feedback` writes, and the annotation has to say so or a client will
    # treat it as safe to retry and to call speculatively. It is not
    # destructive: every write is a new append-only record under a
    # content-addressed name, so a retry collapses into the record it already
    # wrote (PLAN.md §3.7). `idempotent_hint` is that promise, declared.
    appends = ToolAnnotations(read_only_hint=False, destructive_hint=False,
                              idempotent_hint=True)

    def _open() -> Optional[Index]:
        return Index(index_path) if index_path.exists() else None

    def _current_shas(idx: Index) -> dict[str, str]:
        """Where the source repos are now, if a clone is reachable."""
        if cache_dir is None:
            return {}
        from librarian.scan import commit_sha
        out = {}
        for repo in idx.repo_shas:
            root = cache_dir / repo
            if (root / ".git").exists():
                try:
                    out[repo] = commit_sha(root)
                except Exception:
                    pass
        return out

    @server.tool(annotations=read_only)
    def kb_search(question: str, caller_profile: str = "neutral",
                  limit: int = 10,
                  require_evidence: Optional[list[str]] = None) -> dict[str, Any]:
        """Search the knowledge base under a named caller profile.

        `caller_profile` selects a stored, versioned query profile -- for the
        microscope, `ms:lens-5-photo-perturbation` or `ms:lens-4-sample-optics`.
        The same question deliberately returns different results under each,
        because the two lenses own different evidence. Use `neutral` when no
        lens applies.

        Terms of three characters or more are matched and bm25-ranked; shorter
        ones fall back to a case-sensitive substring match, so `NA` finds the
        numerical aperture and `na` does not.

        `require_evidence` is a hard filter and is off by default. Filtering on
        it removes every document that carries no tier, which includes all of
        `docs/` -- ask for it only when a tier is genuinely required.

        Each hit carries `repo@sha:path#locator`. Cite that, not the snippet.

        `profile_candidates` says which profile the question's own words point
        at, each citing the **agent file** that declares it. It is **applied to
        nothing** -- `candidates_applied` is always false and the hits above
        were ranked by the profile you declared. Re-ask under a candidate if one
        fits; the choice is yours to make and to record, because a profile
        inferred here would change the evidence returned with nothing in the
        answer showing it was inferred. An empty list means no owner declares
        the question's words uniquely, which is an answer.
        """
        idx = _open()
        if idx is None:
            return NO_INDEX
        try:
            profiles = load_profiles(profiles_dir)
            if caller_profile not in profiles:
                # The branch PLAN.md 5.3 was written about: a list of ids
                # and nothing to choose by. The candidates are cited, so a
                # caller that guessed a name wrong gets a reason rather than
                # a menu -- and still picks for itself.
                return {"status": "unknown_profile", "asked_for": caller_profile,
                        "known": sorted(profiles),
                        "profile_candidates": [
                            {"profile": c.profile, "because": c.because,
                             "declares": c.declares,
                             "matched_terms": list(c.matched_terms),
                             "score": round(c.score, 4)}
                            for c in idx.profile_candidates(question, profiles)],
                        "candidates_applied": False}
            res = idx.search(question, profiles[caller_profile], limit=limit,
                             current_shas=_current_shas(idx),
                             require={"evidence": require_evidence}
                             if require_evidence else None,
                             profiles=profiles)
            out = res.as_dict()
            out["notes"] = [EMPTY_NOTE, STALE_NOTE, TIER_NOTE]
            return out
        finally:
            idx.close()

    @server.tool(annotations=read_only)
    def kb_get(uid: str) -> dict[str, Any]:
        """One document in full, with its outbound and inbound references.

        `uid` is `repo:path#locator` as returned by `kb_search`. A uid that is
        not present returns `status: not_found` together with the other sections
        of that path, because the usual reason a uid misses is that a heading
        was edited and the locator moved.
        """
        idx = _open()
        if idx is None:
            return NO_INDEX
        try:
            d = idx.get(uid)
            return d or {"status": "not_found", "uid": uid, "near": []}
        finally:
            idx.close()

    @server.tool(annotations=read_only)
    def kb_neighbors(uid: str, relation: str = "cites",
                     direction: str = "out") -> dict[str, Any]:
        """Documents one hop away in the reference graph.

        `relation` is `cites`, `supersedes`, `superseded_by`, `applies_to` or
        `same_file`. `direction` is `out`, `in` or `both`.

        A neighbour whose `status` is not `indexed` is a reference whose target
        exists in the repository but is not indexed, or is absent entirely. The
        second kind is a defect in the citing entry and is reported by
        `kb_stale` as `broken_cross_reference`.
        """
        idx = _open()
        if idx is None:
            return NO_INDEX
        try:
            return {"status": "ok", "uid": uid, "relation": relation,
                    "direction": direction,
                    "neighbors": idx.neighbors(uid, relation, direction)}
        except ValueError as e:
            return {"status": "bad_request", "detail": str(e)}
        finally:
            idx.close()

    @server.tool(annotations=read_only)
    def kb_supplies(name: str) -> dict[str, Any]:
        """What supplies a registry field, or what a gate is waiting for.

        `name` is either a field (`bleach_photons`) or a gate (`G10`) -- the same
        question asked from either end.

        `status: blocked` means no entry supplies the field anywhere, so the gate
        cannot compute. That is the answer, not a malfunction: the microscope
        returns `BLOCKED` by design when an input is missing, and the useful
        response is to report which input.
        """
        idx = _open()
        if idx is None:
            return NO_INDEX
        try:
            return {"status": "ok", **idx.supplies(name)}
        finally:
            idx.close()

    @server.tool(annotations=read_only)
    def kb_inputs(computation: str, repo: str = "ms") -> dict[str, Any]:
        """What a computation needs, and which of it exists — one call.

        `computation` is a function name in the source repository, e.g.
        `radial_stiffness_n_per_m`. The answer is the **scalar closure of its
        signature**: every argument, expanded through the dataclasses it names,
        with where each one comes from and whether anything supplies it.

        Ask this instead of `kb_search` when the question is *"what do I need in
        order to compute X"*. Search ranks documents about a topic; this
        enumerates inputs, and no ranking can reach an answer that is a closure
        over a signature.

        `status` is `ready`, `blocked` or `unresolved`, and `blocked` outranks
        `unresolved` because a named missing input is actionable and a missing
        mapping is not. Per input:

          ready       a registry supplies it, and at least one entry is filled
          blocked     the field exists and no entry fills it — report the field
          unresolved  no registry field carries that name and no alias bridges
                      it. `candidates` holds ranked documents that mention it,
                      and `candidate_query` says what was searched, because a
                      one-character field name like `n` cannot be a query and
                      the class that declares it is searched instead

        `via_alias` means the link needed a recorded mapping rather than a name
        match — a radius is not a diameter and the units differ. Those aliases
        are verified against the registries on every build.
        """
        idx = _open()
        try:
            from librarian.inputs import recipe
            root = (cache_dir or Path("cache")) / repo
            if not root.is_dir():
                return {"status": "no_checkout", "detail": f"cache/{repo} is absent"}
            r = recipe(root, computation, index=idx,
                       aliases_path=profiles_dir / "_field-aliases.yaml")
            if r is None:
                return {"status": "not_found", "computation": computation,
                        "detail": f"no function of that name in cache/{repo}"}
            return r.as_dict()
        finally:
            if idx:
                idx.close()

    @server.tool(annotations=read_only)
    def kb_gaps(missing_only: bool = True) -> dict[str, Any]:
        """Registry coverage: which gate is BLOCKED, for want of which field.

        Derived by crossing three declarations -- what a registry declares in its
        own schema comment, what a gate function actually reads, and what an
        entry holds as a non-empty value. `filled/total` stays over the whole
        registry even when only unfilled rows are shown, because "0 of 6" and
        "0 of 0" say different things.
        """
        idx = _open()
        if idx is None:
            return NO_INDEX
        try:
            return {"status": "ok", "rows": idx.gaps(missing_only=missing_only)}
        finally:
            idx.close()

    @server.tool(annotations=read_only)
    def kb_stale() -> dict[str, Any]:
        """Is the index behind, and does what is declared still match what exists?

        Two different questions, both answered here.

        `index_stale` compares the SHA each repository was indexed at against
        where it is now. `findings` is the drift report computed at build time:
        gates declared with a threshold and implemented nowhere, generated files
        outliving their generator, declared counts that disagree with the files,
        entries carrying no falsifier, and references whose target is absent.

        An entry with no falsifier cannot be challenged, which is a defect in
        the entry rather than a limitation here.
        """
        idx = _open()
        if idx is None:
            return NO_INDEX
        try:
            current = _current_shas(idx)
            return {
                "status": "ok",
                "indexed_at": idx.repo_shas,
                "current": current,
                "index_stale": idx.is_stale(current),
                "doc_count": int(idx.meta.get("doc_count", 0)),
                "links": idx.link_counts(),
                "findings": idx.findings(),
                "entry_defects": idx.entry_defects(),
            }
        finally:
            idx.close()

    @server.tool(annotations=appends)
    def kb_feedback(query: str, caller_profile: str, verdict: str,
                    returned: Optional[list[str]] = None,
                    cited: Optional[list[str]] = None,
                    missing: Optional[list[str]] = None,
                    asked_by: str = "agent", action: str = "none",
                    action_ref: Optional[str] = None,
                    note: Optional[str] = None) -> dict[str, Any]:
        """Record which hits a search actually answered with. **This writes.**

        One call is one session under `kb/08-retrieval/sessions/`, which is
        local and never committed. Nothing in any source repository is touched.

        **Report `cited` -- the uids you actually used.** It is a fact, and it
        is the only thing here that improves retrieval: retrieval has no
        grader, so a past confirmed citation stands in for one. It is never
        inferred from what you were sent, because inferred it stops being a
        fact. `cited` must be a subset of `returned`; what you needed and did
        not get goes in `missing`.

        `verdict` separates causes, because the fix differs by cause:
        `useful` · `wrong_ranking` (the fix is in `profiles/`) ·
        `missing_entry` (in `kb/`) · `wrong_tier` (the entry's frontmatter) ·
        `no_result` (tokenizer or adapter). **`not_searched` is not accepted**:
        it is the default of a query nobody recorded, and calling this is the
        record that someone looked.

        `asked_by` is a role -- `agent`, or a `human:*` profile -- and never a
        name. `note` is prose for a person to read; no code branches on it, so
        do not put a number or a status in it.

        There is deliberately **no satisfaction score**. A score makes
        averaging possible, and averaged, 20 ranking failures and 20 missing
        entries are the same number while their fixes live in different files.

        Calling twice with the same report is safe: the record is named by a
        digest of its content, so the second call returns the first one's id
        with `created: false`.

        Returns `promotion_status`, which is how far this query is from
        becoming a regression oracle. **It promotes nothing.** Promotion needs
        the same result under two distinct index states *and* human approval --
        an agent promoting its own retrieval results to ground truth is a
        self-confirming loop, and the approval is the only damping on it.
        """
        if sessions_dir is None:
            return {"status": "no_session_store",
                    "detail": "this server was registered without a sessions "
                              "directory, so it has nowhere to write."}
        idx = _open()
        if idx is None:
            return NO_INDEX
        try:
            from librarian.feedback import (FeedbackError, promotion_status,
                                            record_id, session, write)
            profiles = load_profiles(profiles_dir)
            current = _current_shas(idx)
            try:
                rec = session(
                    query=query, caller_profile=caller_profile, verdict=verdict,
                    returned=returned, cited=cited, missing=missing,
                    asked_by=asked_by, action=action, action_ref=action_ref,
                    note=note,
                    index_sha=idx.repo_shas,
                    index_stale=idx.is_stale(current),
                    known_uids=idx.has_uids(list(returned or [])),
                    known_profiles=set(profiles),
                )
            except FeedbackError as e:
                # A refusal names the rule, not just the field. The caller is a
                # model, and "invalid verdict" gets retried with another guess.
                return {"status": "refused", "detail": str(e),
                        "verdicts": VERDICT_NOTE}
            written = write(sessions_dir, rec, _today())
            return {
                "status": "ok",
                "id": record_id(written),
                "created": written.created,
                "path": str(written.path),
                "committed": False,
                "index_sha": rec["index_sha"],
                "index_stale": rec["index_stale"],
                "promotion_status": promotion_status(
                    sessions_dir, query, caller_profile),
                "notes": [LOCAL_ONLY_NOTE, PROMOTION_NOTE],
            }
        finally:
            idx.close()

    @server.tool(annotations=appends)
    def kb_challenge_raise(target_uid: str, doubt_kind: str,
                           falsifier_cited: str,
                           caller_profile: str = "neutral",
                           note: Optional[str] = None,
                           gpu_hours: float = 0, instrument_hours: float = 0,
                           search_budget_spent: float = 0,
                           in_reply_to: Optional[str] = None) -> dict[str, Any]:
        """Raise a doubt against a claim, as a work order. **This writes.**

        **`falsifier_cited` is mandatory and must point into the target's own
        file** -- the target's own falsification condition, by locator. That is
        what makes this a work order rather than an argument, and a citation
        landing anywhere else is refused: a challenge may not cite a new basis.

        `doubt_kind` is what routes the challenge, and nothing else does --
        not who raised it:

          `superseded_by_measurement`  the published number does not transfer
                                       to this setup      -> ms
          `contradicted_by_run`        the claim is contradicted by what the
                                       model does         -> bd
          `conditions_not_met`         the conditions of validity were never
                                       checked            -> research-topic
          `scope_exceeded`             used outside the scope it stated
                                                          -> a human
          `never_verified`             names no falsifier at all -> a human,
                                       who can re-raise it with one that does

        **An entry carrying no falsification condition cannot be challenged.**
        That is a defect in the entry, not a limit here: every judgment is
        supposed to carry the check that would overturn it. The fix is a pull
        request against the repository that holds it.

        `depth` increments against `in_reply_to`, and past the bound a
        challenge goes to a person whatever its doubt kind. Unbounded, doubt
        circulates instead of resolving. Record `gpu_hours`,
        `instrument_hours` and `search_budget_spent` honestly: unrecorded, the
        budget stops being a budget and becomes the retirement decision.

        Nothing here settles anything. `state` is `routed`, `resolved_by` is
        null, and `upheld`/`rejected` is set later by what a run, a measurement
        or a search returned -- never by a vote.
        """
        if challenge_dir is None:
            return {"status": "no_challenge_store",
                    "detail": "this server was registered without a challenge "
                              "directory, so it has nowhere to write."}
        idx = _open()
        if idx is None:
            return NO_INDEX
        try:
            from librarian.challenge import (ChallengeError, challenge,
                                             depth_of, open_against, record_id,
                                             write)
            target = idx.get(target_uid)
            try:
                rec = challenge(
                    target_uid=target_uid, doubt_kind=doubt_kind,
                    falsifier_cited=falsifier_cited,
                    caller_profile=caller_profile, note=note,
                    cost={"gpu_hours": gpu_hours,
                          "instrument_hours": instrument_hours,
                          "search_budget_spent": search_budget_spent},
                    in_reply_to=in_reply_to,
                    target=target,
                    falsifier_exists=idx.get(falsifier_cited) is not None,
                    prior_depth=(depth_of(challenge_dir, in_reply_to)
                                 if in_reply_to else None),
                )
            except ChallengeError as e:
                return {"status": "refused", "detail": str(e),
                        "doubt_kinds": DOUBT_KINDS_NOTE}
            standing = open_against(challenge_dir, target_uid)
            written = write(challenge_dir, rec, _today())
            out = {
                "status": "ok",
                "id": record_id(written),
                "created": written.created,
                "path": str(written.path),
                "target": rec["target"],
                "routed_to": rec["routed_to"],
                "resolvable_by": rec["resolvable_by"],
                "state": rec["state"],
                "depth": rec["depth"],
                "already_standing": [r.get("doubt_kind") for r in standing],
                "notes": [ROUTING_NOTE],
            }
            if rec["resolvable_by"] == "literature":
                # The one thing this repository settles, and it answers a
                # weaker question than the challenge asked.
                out["locator_exists"] = True
                out["verdict"] = "unknown"
                out["notes"].append(LITERATURE_NOTE)
            if "escalated_at_depth" in rec:
                out["escalated_at_depth"] = rec["escalated_at_depth"]
            return out
        finally:
            idx.close()
