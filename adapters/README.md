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

## The assertion every adapter carries

**A non-zero document count for its source.** A source that drops to zero fails
the build rather than reporting nothing.

This is not defensive habit. BD recorded the accident: `tools/kb.py` pointed at a
renamed path and *"simply reported 'run-less knowledge 0' for 126 existing
entries. A silently empty read is the same failure mode as an unwired checker."*
