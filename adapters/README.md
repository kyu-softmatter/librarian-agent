# `adapters/` — one parser per repository contract

An adapter flattens a source format into the single `doc` row defined in
[../PLAN.md](../PLAN.md) §4.1, keeping branchable fields physically separate from
prose.

**Parse the declared contract; do not hard-code paths.** Each repository states
its own machine contract, and BD `wiki/CLAUDE.md` gives the instruction directly.
Hard-code a path and the next folder rename produces a silently empty read.

| Source | Contract to parse | v1 |
|---|---|---|
| MS `kb/` | entry frontmatter; `literature/_template.md` | ✅ |
| MS `data/*.yaml` | the registry field a gate consumes, and whether it is empty | ✅ |
| MS `docs/` | section anchors as locators | ✅ |
| MS `.claude/agents/` | lens number, owned gates, declared tools -> `map/04-agents/ms/` | ✅ |
| BD `wiki/` | `knowledge/wiki/CLAUDE.md` frontmatter contract, read from the file | ✅ |
| BD `source/` | the same contract's `source_frontmatter_*` and `source_kinds` | ✅ |
| BD `entries/` | `bdbot.kb_entry/0.1`, decomposed over `lessons[]` | ✅ |
| BD `runs/` | `bdbot.record/0.1` — index only, never migrated | v2 |
| RT `design/` | `kb-schema.md` §4.1-4.7 | v3 |

**A source name is prefixed with the repository it parses**, and
`librarian.scan.sources_for` selects on that prefix. Without the convention a
scan of one checkout runs every adapter against it, and `source_empty` — the
check that catches a store which should have answered and did not — fires at
error severity on every run instead.

## Built, and what it produces

Measured 2026-09-09 against `agentic-microscope` @ `fbedef0` and
`Brownian-Dynamics-Agent` @ `ad1267b`:

| Adapter | Files | Documents |
|---|---|---|
| `ms_kb` | 45 | 298 |
| `ms_data` | 8 | 86 |
| `ms_docs` | 10 | 95 |
| `ms_agents` | 5 | 75 |
| **ms** | **68** | **554** |
| `bd_wiki` | 45 | 370 |
| `bd_source` | 45 | 273 |
| `bd_entries` | 144 | 144 |
| **bd** | **234** | **787** |
| **one index** | **302** | **1341** |

    python -m librarian.cli scan    --repo ms
    python -m librarian.cli reindex --repo ms --repo bd

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
