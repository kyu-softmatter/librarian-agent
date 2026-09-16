# `mcp_server/` — the MCP server

**Seven read tools and two writes** — the whole surface PLAN.md §5.2 declares.
**Writes touch `kb/` and `store/` only**: nothing in a source repository is
written, ever, and anything that has to land there arrives as a pull request. A
challenge is *handed to* whoever can run the falsifier; it is not applied to
their files.

| Tool | Purpose |
|---|---|
| `kb_search` | ranked hits with coordinates, tier and falsifier — plus `profile_candidates`, which profile the question's own words point at, each citing the agent file that declares it and **applied to nothing**. Built: `librarian/index.py` |
| `kb_inputs` | what a computation needs, and which of it exists — the closure over a signature. Built: `librarian/inputs.py` |
| `kb_get` | one entry, body and frontmatter |
| `kb_neighbors` | `cites` / `used_by` / `supersedes` graph |
| `kb_supplies` | what supplies a registry field or a gate |
| `kb_gaps` | gates `BLOCKED` for want of an input — **v1's primary product**. Built: `librarian/gaps.py` |
| `kb_stale` | the drift report. Built: `librarian/drift.py` |
| `kb_challenge_raise` | **writes.** Doubt against a claim, routed by the type of the falsifier it cites — never by who raised it. Built: `librarian/challenge.py` |
| `kb_feedback` | **writes.** One retrieval session — which hits were actually cited. Local and never committed. Built: `librarian/feedback.py` |

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
`python3` is not normally on PATH there, and **Windows is the deployment
platform**: every system runs on the microscope PC, which is also the machine
holding the acquisition archive ([../PLAN.md](../PLAN.md) decision 35). macOS is
the development environment, so both lines get used.

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

**stdio is correct, and it stays correct through BD.** It said the opposite
here until 2026-09-15: that BD's repository sat on another machine, that
knowledge only accumulates over stdio when the SQLite file is on the caller's
own disk, and that an always-on service on the lab NAS followed. The premise
was wrong — BD's macOS is a development environment, it passes CI, and **all
four systems run on the microscope PC** (decision 35). One machine is exactly
what the stdio column was always right for.

**Concurrent reads are already safe; writes are what is left.** Several agents
mean several spawned processes over one SQLite file. `_open()` connects
`mode=ro` and **per call**, closing again before returning, so no session pins a
handle and a `reindex` lands on the next call — a call that arrives mid-rebuild
gets `status: no_index`, which is the designed degradation rather than a wrong
answer. Writes needed a policy and now have one that is not a service:
`librarian/record.py` names a record by a sha256 of its content and creates it
with `os.link` from a complete temp file, so a retry is idempotent and a
concurrent reader sees a whole record or none. `build()` moves the index in by
`os.replace` for the same reason, which is why the `no_index` answer above now
covers only the interval before an index has ever been built
([../PLAN.md](../PLAN.md) §3.7). The shared registration form stays open — one
machine does not make MS's absolute interpreter path portable.

**People reach it the same way, and nothing here composes an answer for them.** A
person arrives through their own MCP client under a `human:*` role profile, so
the model they are already talking to does the composing while this server keeps
returning quoted text with coordinates. That holds wherever it runs, which is
why the host correction above changed nothing in this paragraph
→ [../PLAN.md](../PLAN.md) §3.5.

## A challenge is a work order, not an argument

`kb_challenge_raise` routes by **the type of the falsifier it cites** — a
measurement to the microscope, a run to the simulator, an unchecked condition of
validity to research-topic, and none available to a person. Never by who raised
it: `raised_by` is recorded and no code reads it.

Two refusals carry the weight, and both look like the tool failing:

- **A citation outside the target's own file.** `falsifier_cited` has to point
  into the claim being doubted. Citing a new basis instead is `T-048`'s
  prohibited move, and it puts a mass of counter-argument back in the slot rt
  emptied on purpose.
- **An entry carrying no falsification condition cannot be challenged at all.**
  That is a **defect in the entry** — every judgment is supposed to carry the
  check that would overturn it — and the fix is a pull request against the
  repository holding it, not a workaround here. `kb_stale` reports the same
  entries as defects.

On the `literature` route this server settles one thing: whether the cited
locator exists. The verdict stays `unknown`, because resolving it means someone
reading a paper, which is what `I-052` forbids of a gate. rt records that route
as `C-007`, considered this exact escape and did **not** adopt it; it is adopted
here because it is deterministic and answers a weaker question than the
challenge asked.

## What is not here

**Promotion.** `sessions/ → oracles/` is human-approved
and deliberately not a tool: an agent promoting its own retrieval results to
ground truth is a self-confirming loop, and the approval is the only damping on
it. `python -m librarian.cli sessions` is the view that approval is given
against — it reports which questions meet every condition but that one, and
promotes nothing.
→ [../PLAN.md](../PLAN.md) §6.1 · §3.7 · [../FEEDBACK.md](../FEEDBACK.md) §5
