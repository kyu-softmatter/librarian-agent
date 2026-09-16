# `adapters/` — one parser per repository contract

An adapter flattens a source format into the single `doc` row defined in
[../PLAN.md](../PLAN.md) §4.1, keeping branchable fields physically separate from
prose.

**Parse the declared contract; do not hard-code paths.** Each repository states
its own machine contract, and BD `wiki/CLAUDE.md` gives the instruction directly.
Hard-code a path and the next folder rename produces a silently empty read.

| Source | Contract to parse | v1 |
|---|---|---|
| MS `kb/` | entry frontmatter; `literature/_template.md`; `plans/` and `sessions/` pinned to no evidence tier; generated `kb/INDEX.md` excluded | ✅ |
| MS `data/*.yaml` | the registry field a gate consumes, and whether it is empty | ✅ |
| MS `docs/` | section anchors as locators | ✅ |
| MS `.claude/agents/` | lens number, owned gates, declared tools. **This is the layer that makes four declaration forms comparable** — into one `Doc`, not into a generated folder (decision 38) | ✅ |
| BD `wiki/` | `knowledge/wiki/CLAUDE.md` frontmatter contract, read from the file | ✅ |
| BD `source/` | the same contract's `source_frontmatter_*` and `source_kinds` | ✅ |
| BD `entries/` | `bdbot.kb_entry/0.1`, decomposed over `lessons[]` | ✅ |
| BD `runs/` | `bdbot.record/0.1` — index only, never migrated | v2 |
| RT `design/ideas.md` | the item log's own *"Rules for this document"* — one document per `T-`/`C-`/`Q-` id, **and the ID is the locator** | ✅ |
| RT `README.md` + `design/` | section anchors; `personas/V[12]-*.md` as agents, keyed on the pole | ✅ |

**A source name is prefixed with the repository it parses**, and
`librarian.scan.sources_for` selects on that prefix. Without the convention a
scan of one checkout runs every adapter against it, and `source_empty` — the
check that catches a store which should have answered and did not — fires at
error severity on every run instead.

## Built, and what it produces

Measured 2026-09-15 against `agentic-microscope` @ `9f971a8` and
`Brownian-Dynamics-Agent` @ `a18e171`:

| Adapter | Files | Documents |
|---|---|---|
| `ms_kb` | 51 | 370 |
| `ms_data` | 8 | 86 |
| `ms_docs` | 10 | 95 |
| `ms_agents` | 5 | 75 |
| **ms** | **74** | **626** |
| `bd_wiki` | 49 | 402 |
| `bd_source` | 45 | 273 |
| `bd_entries` | 145 | 145 |
| **bd** | **239** | **820** |
| `rt_ideas` | 1 | 76 |
| `rt_design` | 7 | 62 |
| **rt** | **8** | **138** |
| **one index** | **321** | **1584** |

**rt is 8 files and 138 documents, and 65 of those are one table.** Its
`design/ideas.md` is the item log this repository cites as grounds throughout,
and the unit there is a **table row with an ID** rather than a section — so
`rt_ideas` makes the ID the locator, and `C-001` is `rt@sha:design/ideas.md#C-001`.
Until that existed, every `T-0xx` and `C-0xx` in this repository's own design
documents was a citation with nowhere to walk back to.

**63 of `ms_kb`'s 72 new documents come from two stores MS added and this
adapter did not know**: `kb/plans/` (29) and `kb/sessions/` (34). The rest are
entries upstream added to stores already covered. Both new stores were being
skipped in silence until the coverage check named their files, which is that
check earning its keep rather than a clean result.

    python -m librarian.cli scan    --repo rt
    python -m librarian.cli reindex --repo ms --repo bd --repo rt

> **These figures move when a source repository does, and they already have.**
> This table read *59 files, 544 documents* against `ms@196cdf1` while the
> top-level README read **513** for the same commit and the same 59 files —
> `librarian.index.build` filters nothing, so at most one was ever right, and
> the disagreement was never resolved. Both are now superseded by measurement
> rather than settled: the microscope has moved to `fbedef0`, and neither figure
> describes its corpus. A count written beside a tool that can compute it is the
> stale-table problem, which is why the command is printed above the table.

The analyses that consume these live one level up, in `librarian/`, because they
ask questions **across** sources rather than parsing any one of them:
`gaps.py` (which gate is BLOCKED for want of which field) and `drift.py` (does
what is declared still match what exists).

## The assertion every adapter carries

**A non-zero document count for its source**, and coverage checked **from
outside** the adapter: candidate files are enumerated independently in
`librarian/scan.py`, and any candidate that produced no document is reported. An
adapter that counted its own output would pass while silently dropping a folder.

This is not defensive habit. BD recorded the accident: `tools/kb.py` pointed at a
renamed path and *"simply reported 'run-less knowledge 0' for 126 existing
entries. A silently empty read is the same failure mode as an unwired checker."*
