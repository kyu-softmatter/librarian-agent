# `mcp_server/` — the MCP server

Six read tools and two write tools. **Writes touch `kb/` and `store/` only** —
nothing in a source repository is written, ever; anything that has to land there
arrives as a pull request.

| Tool | Purpose |
|---|---|
| `kb_search` | ranked hits with coordinates, tier and falsifier. Built: `librarian/index.py` |
| `kb_get` | one entry, body and frontmatter |
| `kb_neighbors` | `cites` / `used_by` / `supersedes` graph |
| `kb_supplies` | what supplies a registry field or a gate |
| `kb_gaps` | gates `BLOCKED` for want of an input — **v1's primary product**. Built: `librarian/gaps.py` |
| `kb_stale` | the drift report. Built: `librarian/drift.py` |
| `kb_challenge_raise` | writes `store/challenge/`, routes by falsifier type |
| `kb_feedback` | writes `kb/08-retrieval/sessions/` |

## Why the folder is not called `mcp/`

The SDK's package is `mcp`, and `python -m` puts the working directory first on
`sys.path`. A local `mcp/` therefore shadows it and
`from mcp.server.mcpserver import MCPServer` fails with
`No module named 'mcp.server'` — from inside the repository only, which is the
worst place for a failure to appear. `agentic-microscope` calls its own
`mcp_server/` for the same reason.

## Three invariants on every response

1. **Coordinates.** Every hit carries `repo@sha:path#locator`. A hit without them
   is not returned.
2. **Tier.** Every hit carries `evidence` and `tier`, so a caller cannot mistake
   an `assumed` value for a measurement. That mistake has a recorded cost: BD's
   `T = 300 K` filed as measured propagated -4% to -14% downstream.
3. **State, not silence.** Zero results is `searched_empty`. Never having looked
   is `not_searched`. A stale index sets `index_stale: true`.

## Registering it

`.mcp.json` at the repository root:

```json
{
  "mcpServers": {
    "librarian": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"]
    }
  }
}
```

The client launches it with the repository root as the working directory, which
is what makes `-m mcp_server.server` resolve. **On Windows use `"python"`** —
`python3` is not normally on PATH there, and the lab machine is the one that has
the acquisition archive.

Install and build the index first; the tools answer `status: no_index` until
there is one, rather than failing:

```bash
pip install -e .
git clone --depth 1 https://github.com/kyu-softmatter/agentic-microscope.git cache/ms
python -m librarian.cli reindex --repo ms
```

## What is not here

`kb_challenge_raise` and `kb_feedback` are the write half of this surface.

A challenge has to route by the type of the falsifier it cites, and a retrieval
record stores raw query text in a repository that is public — what someone was
looking for is what they are about to do — so the publish-gate scope is settled
before either lands. → [../PLAN.md](../PLAN.md) §6.1
