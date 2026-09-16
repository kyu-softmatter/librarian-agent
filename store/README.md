# `store/` — published by Librarian

Not derived and not canonical knowledge: these are things Librarian **issues.**
They are a record, so they are not deleted.

```
challenge/          the retirement mechanism — doubt against a claim, plus its routing
digest/<ISO week>/  weekly refinement output                    [deferred]
crosswalk/          BD paper -> MS quantity, 1 to N             [v2]
inbox/              LLM proposals awaiting human approval
```

## `challenge/`

**A challenge is a work order, not an argument.** It must cite the target entry's
own falsification condition, by locator, pointing **into the target** rather than
into the challenger. `falsifier_cited` is mandatory and a raise without it is
refused.

**Routing is decided by the falsifier's type, not by the sender:**

| The doubt | Falsifier | Routes to |
|---|---|---|
| the published number does not transfer to this setup | a local measurement | **MS** |
| the claim is contradicted by what the model does | a run | **BD** |
| the conditions of validity were never checked | literature | **research-topic** |
| used outside the scope it stated | none available | **a human** |

`upheld` / `rejected` is set by what a run, a measurement or a search returned —
**never by a vote**, and `not_run` is the default.

**Librarian may settle only one thing:** for the literature route, whether the
cited locator exists and states the condition. Everything else returns `unknown`.

## How a record is written

**Append-only, and two writers never contend** — [../PLAN.md](../PLAN.md) §3.7,
`librarian/record.py`. Nothing here is ever updated in place: a correction is a
new record that supersedes the old one, which is the same way custody models
retirement everywhere else.

A filename is `<date>-<slug>-<sha256[:8]>`, where the digest is over the
canonical record. Two consequences, and both are the policy rather than
implementation detail:

- **A retried call is one record, not two.** The same content gets the same
  name, the name is created exclusively, and the second write is a no-op. This
  matters most for `kb/08-retrieval/`: oracle promotion requires a session
  reproduced under **two distinct `index_sha`**, and a retry landing twice would
  let one caller satisfy a check built to need two index states.
- **A reader sees a whole record or none.** The bytes go to a sibling temp file
  and the final name is created as a hard link to it, so a concurrent `scan()`
  never reads a prefix.

**There is no generated index over these folders, by decision.** A rollup two
writers both append to is the one shape that would need a lock — and it is also
BD's `knowledge/source/papers/INDEX.md`, headed *do not edit by hand*, naming a
generator that is not in the repository and stating 40 entries where 42 files
exist. That file is why this repository exists. The listing is derived when it
is read.

## `inbox/`

**Nothing leaves this folder without human approval.** The LLM refinement step
emits citations and locators; it does not originate or summarize numbers, does
not aggregate across entries, and never assigns `evidence: measured`.
