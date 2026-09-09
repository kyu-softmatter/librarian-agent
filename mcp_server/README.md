# `mcp_server/` — the MCP server

Seven read tools and two write tools. **Writes touch `kb/` and `store/` only** —
nothing in a source repository is written, ever; anything that has to land there
arrives as a pull request.

| Tool | Purpose |
|---|---|
| `kb_search` | ranked hits with coordinates, tier and falsifier. Built: `librarian/index.py` |
| `kb_inputs` | what a computation needs, and which of it exists — the closure over a signature. Built: `librarian/inputs.py` |
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

## Transport and lifetime

`main()` runs `transport="stdio"`: the client spawns one process per session and
it dies with that session. Three things follow, and each is a separate way for
*"the librarian is available"* to be false.

1. **The process has to exist.** No MCP client manages a server's lifetime, so an
   always-on server is systemd's, docker's or a supervisor's job.
2. **Registration happens at startup.** `.mcp.json` is read once, so the set of
   reachable servers is closed for that session.
3. **Every call is independent.** Request-response, no memory between calls —
   whatever has to survive two of them is in `index/kb.sqlite`, or it does not
   exist.

stdio is correct for v1: one indexed repository, one machine, one writer, and no
tool here that writes. It stops being correct at BD, whose repository is on
another machine — knowledge only accumulates over stdio when the SQLite file is
on the caller's own disk. **v2 replaces this with one always-on service on the
lab NAS**, and the shared registration form and the concurrent-write policy
are still open decisions → [../PLAN.md](../PLAN.md) §3.4.

**People reach it the same way, and nothing here composes an answer for them.** A
person arrives through their own MCP client under a `human:*` role profile, so
the model they are already talking to does the composing while this server keeps
returning quoted text with coordinates. That is why a NAS several people can
reach still needs no LLM inside it → [../PLAN.md](../PLAN.md) §3.5.

## What is not here

`kb_challenge_raise` and `kb_feedback` are the write half of this surface.

A challenge has to route by the type of the falsifier it cites, and a retrieval
record stores raw query text in a repository that is public — what someone was
looking for is what they are about to do — so the publish-gate scope is settled
before either lands. → [../PLAN.md](../PLAN.md) §6.1
