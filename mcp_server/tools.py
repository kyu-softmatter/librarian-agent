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

TIER_NOTE = (
    "Every hit carries `evidence` and `advances`. `advances: false` means that "
    "tier cannot advance a verdict -- a literature value never can, by rule. "
    "That is the state of the evidence, not a shortcoming of the result, and it "
    "should be reported rather than worked around."
)


def register(server, index_path: Path, profiles_dir: Path,
             cache_dir: Optional[Path] = None) -> None:
    read_only = ToolAnnotations(read_only_hint=True, destructive_hint=False)

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
        """
        idx = _open()
        if idx is None:
            return NO_INDEX
        try:
            profiles = load_profiles(profiles_dir)
            if caller_profile not in profiles:
                return {"status": "unknown_profile", "asked_for": caller_profile,
                        "known": sorted(profiles)}
            res = idx.search(question, profiles[caller_profile], limit=limit,
                             current_shas=_current_shas(idx),
                             require={"evidence": require_evidence}
                             if require_evidence else None)
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
