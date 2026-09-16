# `kb/08-retrieval/` — self-knowledge

What was asked, and what turned out to answer it. The only canonical knowledge
Librarian holds about itself.

```
sessions/   one query = one formal object            [gitignored]
oracles/    promoted to regression tests (human-approved)
findings/   why a profile fails — the cause, not the symptom
```

    python -m librarian.cli sessions    # what is here, and what each needs
    python -m librarian.cli promote --profile <id> --approve --publish-query <query>
    python -m librarian.cli oracles     # run every committed oracle

**An oracle is a past confirmed citation, re-run.** Retrieval has no grader, so
one stands in for it — which is the whole reason `cited` is the field
`kb_feedback` collects. `within_top` is the worst rank the citation actually
achieved, measured at promotion rather than chosen: chosen, it is either too
loose to trip on a regression or too tight to survive ordinary reranking.

**Schema and rules: [../../FEEDBACK.md](../../FEEDBACK.md).** Read it before
adding anything here — this folder is where the design is most likely to violate
*prose is not state*, and the resolution is specific: store **which hits were
cited**, which is a fact, rather than **whether the answer was good**, which is
not.

> **`sessions/` is local only, and that is settled rather than pending.** It
> stores raw query text in a public repository, and what someone was looking for
> is what they are about to do. A session accumulates automatically: no human
> reads one before it lands, and volume guarantees none ever will, so the
> default has to be safety ([../../PLAN.md](../../PLAN.md) §6.1).
>
> **`oracles/` and `findings/` are committed.** Promotion is human-approved
> already (§5), for anti-self-confirmation reasons — and that approval is also
> the moment a person reads the query text and can judge whether it publishes a
> direction. An oracle carries the raw query because it cannot be re-run
> without it; a finding must not, because a finding names the cause and a
> quoted query is the symptom.
>
> The cost, stated here rather than discovered later: **a query that reveals a
> direction cannot be promoted.** It stays a session — still a usable
> regression check for whoever holds it, and one CI will never run.
>
> `librarian/publish.py` is the boundary in code; `tests/test_publish_gate.py`
> asserts the `.gitignore` agrees with it.

No `cards/` — the unit here is a transaction, not a claim.

**One session is one file, written once.** `librarian/record.py` names it by a
sha256 of its own content, so a retried `kb_feedback` collapses into the record
it already wrote instead of becoming a second one. That is not tidiness: §5's
promotion gate requires a session reproduced under **two distinct `index_sha`**,
and a duplicate would let one caller clear a check designed to need two
([../../PLAN.md](../../PLAN.md) §3.7).
