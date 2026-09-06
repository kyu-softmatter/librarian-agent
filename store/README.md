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

## `inbox/`

**Nothing leaves this folder without human approval.** The LLM refinement step
emits citations and locators; it does not originate or summarize numbers, does
not aggregate across entries, and never assigns `evidence: measured`.
