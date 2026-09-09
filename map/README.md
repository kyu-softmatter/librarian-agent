# `map/` — derived

**Regenerated in full. Never hand-edited. Safe to delete.**

```
04-agents/     the structure and function of each (sub)agent
  ms/            5 lenses . 8 gate modules . G1-G32
  bd/            9 agents . 6 skills . 4 rules . A1-A10        [v2]
  rt/            personas V1/V2 . J1-J3 . the boundary table   [v3]
  lib/           this repository: profiles . the tool surface  [v2]
manifest.json  {repo: sha, built_at, doc_count}
```

**Every generated file heads with its generator path and the commit SHA it was
built from.** Without that header a generated file outlives its generator, which
is the state BD's `INDEX.md` is in.

`manifest.json` is also the staleness reference: when its recorded SHA differs
from the current one, every search response carries `index_stale: true`
([../BUILD.md](../BUILD.md) §4-D).

**`lib/` is generated from different files than the other three.** This
repository has no `.claude/agents/`; what declares its roles is `profiles/` (who
may ask what, and how it is weighted) and `mcp_server/`'s tool surface with its
instructions (what may be answered at all). The four repositories each declare
their agents in a different form, which is why this layer exists rather than a
naming convention → [../PLAN.md](../PLAN.md) §3.6.

**The map licenses the correspondence, not the choice.** It is what lets a
response say *which lens declares `G10`* — read off an agent file, at a locator.
It is **not** a way to infer which profile a question belongs to: a guessed
profile changes the evidence returned and nothing in the answer shows it was
guessed (PLAN §3.6, decision 31).
