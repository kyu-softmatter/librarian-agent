# `demo/` — three pages over the live server

**Presentation only. Nothing here is read by the librarian, and deleting the
folder loses nothing.** It exists because the tool surface is seven JSON-RPC
calls and a person in a room needs to see what they answer.

```bash
python demo/serve.py            # http://127.0.0.1:8931/
```

| Page | What it is | Live? |
|---|---|---|
| `search.html` | one box, one question, ranked hits with `repo@sha:path#locator` | **yes** — calls `kb_search` |
| `live.html` | the seven read tools, one button each, request and response side by side | **yes** |
| `index.html` | a one-screen summary of the last build | **no** — figures are baked in |

`index.html`'s numbers are a snapshot and will disagree with the server the
moment a source repository moves. That is the stale-table problem this project
polices, so the page prints the commands it came from and says so in its own
footer rather than pretending otherwise. The two live pages cannot go stale:
they ask.

## Why the launcher is here and not in `mcp_server/`

Decision 26 pins v1's transport to **stdio**, and `mcp_server/server.py` runs
exactly that. `serve.py` imports the same `build()` and runs it over
`streamable-http` instead — the server is byte-identical, only the transport
argument differs. So this is a **preview of the always-on service** PLAN.md §3.4
describes, kept out of the package it previews.

Two transport options make the endpoint reachable from a browser at all:
`json_response` returns plain JSON instead of an event stream, and
`stateless_http` means one self-contained POST per call with no session to hold.
The pages are mounted at the same origin, so there is no CORS hop and no proxy.

## `/log` is a preview of `kb_feedback`, not `kb_feedback`

That tool is one of the two unbuilt writes, and it is unbuilt because the
publish-gate scope is open (PLAN.md §6.1, open decision (a)): a retrieval record
stores raw query text and this repository is public. So the record is written by
the launcher, to `kb/08-retrieval/sessions/`, which `.gitignore` already excludes
for that reason — **no write tool is added to the server, and nothing recorded
here is committed.**

The record follows [FEEDBACK.md](../FEEDBACK.md) §2, including the parts that
constrain it:

- **`verdict` defaults to `not_searched`.** An unrecorded query is not "it was
  fine", it is "this was never checked".
- **`cited` is reported, never inferred** (decision 19). A search writes it
  empty; pressing *cite* is a second, explicit call. Cited from the top two is
  `useful`; cited from further down is `wrong_ranking` — the same hit, and a
  different thing to fix.
- **There is no rating.** [FEEDBACK.md](../FEEDBACK.md) §4 prohibits a scalar
  satisfaction score: stored, it becomes a claim that one entry matters more,
  which is `value_score` returning in new dress.
- A `verdict` outside the vocabulary is refused rather than stored.
