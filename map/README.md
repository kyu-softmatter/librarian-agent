# `map/` — derived

**Regenerated in full. Never hand-edited. Safe to delete.**

```
manifest.json  {repo: sha, doc_count, schema_version}
```

One file. `manifest.json` is the staleness reference: when its recorded SHA
differs from the current one, every search response carries `index_stale: true`
([../BUILD.md](../BUILD.md) §4-D).

---

## `04-agents/` was here, and it is retired

**Retired 2026-09-15, decision 38.** This README described a four-way layer —
`ms/` · `bd/` · `rt/` · `lib/` — holding *"the structure and function of each
(sub)agent"*, with the rule that every generated file heads with its generator
path and the commit SHA it was built from.

**Nothing ever generated it.** The tree held three empty directories and no
`lib/` at all, while this file, `PLAN.md` §3.6, `README.md`, `kb/README.md`,
`TREE.md` and `adapters/README.md` all described it as existing — `README.md`
said it *"already carries the microscope's five lenses with the gates each one
owns."*

That is one step worse than the defect this repository was built to catch. BD's
`knowledge/source/papers/INDEX.md` is a generated file whose generator is
missing; this was a **described artefact that never existed**, and six documents
asserted it.

### Why retiring it is right, and not just cheaper

The layer had one licence: *"report which lens declares `G10`"* — read off an
agent file, **at a locator** ([../PLAN.md](../PLAN.md) §3.6). Three things turn
out to supply that already, and one of them is a reason a map artefact would be
actively worse.

**The adapter is the comparability layer, not a folder.** §3.6's argument for
the map was that *"the four repositories each declare their agents in four
different kinds of file."* True — and `adapters/ms_agents.py` is where those
forms are made comparable, into the one `Doc` row §4.1 defines. BD's nine agents
and rt's two personas arrive the same way, through their own adapters. A folder
of generated markdown would be a second rendering of the same parse.

**The citation has to point at the declaration, not at a copy of it.**
`kb_search`'s `profile_candidates` ([../PLAN.md](../PLAN.md) §5.3) answers *which
lens owns this question* and cites `ms@sha:.claude/agents/sample-optics.md#owns`
— the owner's own file. A map artefact would give a caller something else to
cite, and a response grounded in a generated copy is exactly what this file's
own generator-header rule exists to prevent. The rule was right; the artefact it
was protecting should not exist.

**`lib/` had nothing to add.** Decision 30 put this repository in the fourth
slot, generated from `profiles/` and the tool surface, because it has no
`.claude/agents/`. But what a caller needs from that — which profiles exist, and
what each declares it owns — comes back from `kb_search` itself: `known` on an
unknown profile, and `profile_candidates` with a citation on every query. A
committed file restating it would be self-description with no reader.

### What that leaves

| Question | Answered by |
|---|---|
| Which lens declares `G10` | the index, `kind=agent`, citing the agent file at its locator |
| Which profile owns this question | `kb_search` → `profile_candidates` (§5.3), applied to nothing |
| What supplies a field, or what a gate waits for | `kb_supplies`, from either end (decision 25) |
| Whether an agent file still matches the code | `kb_stale`'s drift report |

`tests/test_map.py` asserts this folder stays one file, so a generator cannot
reintroduce an uncited copy quietly.
