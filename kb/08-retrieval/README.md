# `kb/08-retrieval/` — self-knowledge

What was asked, and what turned out to answer it. The only canonical knowledge
Librarian holds about itself.

```
sessions/   one query = one formal object
oracles/    promoted to regression tests (human-approved)
findings/   why a profile fails — the cause, not the symptom
```

**Schema and rules: [../../FEEDBACK.md](../../FEEDBACK.md).** Read it before
adding anything here — this folder is where the design is most likely to violate
*prose is not state*, and the resolution is specific: store **which hits were
cited**, which is a fact, rather than **whether the answer was good**, which is
not.

> **`sessions/` is not committed yet.** It stores raw query text, and this
> repository is public. What someone was looking for is what they are about to
> do, so the `publish-gate` scope has to be settled first
> ([../../PLAN.md](../../PLAN.md) §6.1). Until then: local only.

No `cards/` — the unit here is a transaction, not a claim.
