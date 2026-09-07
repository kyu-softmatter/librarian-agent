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
| BD `wiki/` + `source/` | `knowledge/wiki/CLAUDE.md` frontmatter contract | v2 |
| BD `entries/` | `tools/kb.py` `SCHEMA_ENTRY` / `ORIGINS` | v2 |
| BD `runs/` | `bdbot.record/0.1` — index only, never migrated | v2 |
| RT `design/` | `kb-schema.md` §4.1-4.7 | v3 |

## Built, and what it produces

Measured against `agentic-microscope` @ `196cdf1`:

| Adapter | Files | Documents |
|---|---|---|
| `ms_kb` | 37 | 267 |
| `ms_data` | 7 | 83 |
| `ms_docs` | 10 | 119 |
| `ms_agents` | 5 | 75 |
| **total** | **59** | **544** |

    python -m librarian.cli scan --repo ms

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
