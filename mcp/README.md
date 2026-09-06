# `mcp/` — the MCP server

Six read tools and two write tools. **Writes touch `kb/` and `store/` only** —
nothing in a source repository is written, ever; anything that has to land there
arrives as a pull request.

| Tool | Purpose |
|---|---|
| `kb_search` | ranked hits with coordinates, tier and falsifier |
| `kb_get` | one entry, body and frontmatter |
| `kb_neighbors` | `cites` / `used_by` / `supersedes` graph |
| `kb_supplies` | what supplies a registry field or a gate |
| `kb_gaps` | gates `BLOCKED` for want of an input — **v1's primary product** |
| `kb_stale` | the drift report |
| `kb_challenge_raise` | writes `store/challenge/`, routes by falsifier type |
| `kb_feedback` | writes `kb/08-retrieval/sessions/` |

## Three invariants on every response

1. **Coordinates.** Every hit carries `repo@sha:path#locator`. A hit without them
   is not returned.
2. **Tier.** Every hit carries `evidence` and `tier`, so a caller cannot mistake
   an `assumed` value for a measurement. That mistake has a recorded cost: BD's
   `T = 300 K` filed as measured propagated -4% to -14% downstream.
3. **State, not silence.** Zero results is `searched_empty`. Never having looked
   is `not_searched`. A stale index sets `index_stale: true`.
