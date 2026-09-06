# Self-knowledge — `kb/08-retrieval/`

Drafted 2026-09-06 · status `draft` · the `kb/08-retrieval/` folder in
[TREE.md](TREE.md)

Purpose: keep a record of **what was asked, and what turned out to answer it**, so
retrieval improves. It is the only canonical knowledge Librarian holds about
itself.

---

## 1. The problem — "a good answer" cannot be state

This store is **where the design is most likely to violate constraint ④** (prose
is not state), because "this answer was good" is a value judgment in natural
language to begin with.

rt `kb-schema.md` §1 names the violation in advance:

> *"Where the violation will happen here is predictable — because a value judgment
> is natural language to begin with. **The sentence 'this topic is interesting'
> cannot be state.**"*

And BD `I-133` found the antipattern in the wild —
`MDCrow/mdcrow/agent/memory.py:119` used **an LLM-written natural-language summary
as state**, and the replacement BD demanded was *"a formal object of the shape
`{engine, config hash, seed, steps completed, checkpoint, observable, convergence
state}`."*

**Storing "this answer was good" as written would reproduce `I-133` in a new
folder.**

---

## 2. The formalization — record the fact, not the judgment

One substitution resolves it.

> **What can be stored is not "it was good" but "which hits were actually cited."**
> The first is a judgment; the second is a fact. And the signal that improves
> retrieval is the second.

`kb/08-retrieval/sessions/<id>.json`:

```json
{
  "id": "ret-8f3a1c02",
  "schema": "librarian.retrieval/0.1",

  "query": "bleach photons for AlexaFluor488 at 470 nm",
  "caller_profile": "ms:lens-5-photo-perturbation",
  "asked_by": "agent",
  "index_sha": "a19c4e7",
  "index_stale": false,

  "returned": ["ms:kb/literature/bleach-photons-af488#verdict",
               "ms:data/fluorophores.yaml#AlexaFluor488",
               "ms:kb/decisions/2026-08-10-labeling-and-laser-recommend#outcome"],
  "cited":    ["ms:data/fluorophores.yaml#AlexaFluor488"],
  "missing":  [],

  "verdict": "missing_entry",
  "action": "none",
  "action_ref": null,

  "note": "found the registry field, but its value is empty so G10 is still BLOCKED"
}
```

### Which fields may be branched on

| Field | Role | Allowed |
|---|---|---|
| `caller_profile` · `verdict` · `action` | routing · verdict | **enums only** |
| `returned` · `cited` · `missing` · `action_ref` | reference | **arrays of uid** |
| `index_sha` · `index_stale` | reproduction conditions | hash · boolean |
| `query` | reproduction input | a string, but **treated as an identifier, not free text** — it is re-executed verbatim |
| `note` | the content of evidence | **prose. No code branches on it** |

The `verdict` vocabulary separates causes, because the fix differs by cause:

| Value | Meaning | Where the fix goes |
|---|---|---|
| `useful` | the cited hit was near the top | — |
| `wrong_ranking` | it was there, but low | `profiles/` |
| `missing_entry` | not in the corpus | `kb/` |
| `wrong_tier` | returned with the wrong tier | the entry's frontmatter |
| `no_result` | the search returned nothing | tokenizer · adapter |
| `not_searched` | **the default** | — |

> **`not_searched` being the default is constraint ①** (rt `kb-schema.md` §4.2:
> *"`not_searched` is the default, not `open`"*). An unrecorded query is not "it
> was fine," it is "this was never checked."
>
> And separating `no_result` from `not_searched` is the answer to
> [BUILD.md](BUILD.md) §1's four-identical-faces problem — returning zero and
> never having looked are different events.

---

## 3. Why `cited` is the key — it becomes a regression oracle

`cited` is a fact, so it can be stored, and **it is simultaneously a test.**

```
oracles/<id>.json  :  (query, caller_profile) → cited must appear in the top N
```

**BD already uses this pattern, and for the same reason.** BD
`knowledge/wiki/CLAUDE.md` (translated):

> *"**Supplying verification oracles** — `benchmarks/` becomes the grounds for
> regression tests run under `pytest`. **Our domain has no grader, so the
> literature stands in for one.**"*

Retrieval has no grader either. **So a past confirmed citation stands in for one.**
That turns [BUILD.md](BUILD.md) §4-B's "a profile actually changes results" from a
claim checked by nine fixtures into one checked by accumulated real use.

---

## 4. Two prohibitions

### ① No scalar satisfaction score

**Forbidden: `profile_satisfaction: 0.82`.**

Exactly rt `kb-schema.md` §3's reason — *a score makes averaging possible, and the
moment you average, divergence is gone.* What is lost here is **which thing failed
and why.** A satisfaction of 0.82 renders 20 `wrong_ranking` events and 20
`missing_entry` events as the same number, when the fix for one is in `profiles/`
and for the other in `kb/`.

**Instead: the list of failing queries, per `verdict`.** Enumeration, not
aggregation.

### ② No branching on `note`

`note` is read by humans. The moment code reads `note` and acts, that is `I-133`.
The check: **is there code that reads this field and branches?** If so, promote it
to an enum or delete it.

---

## 5. Promotion is human-approved — this blocks self-confirmation

```
sessions/  ──(human approval)──▶  oracles/
```

**Inherited from BD's `promotion: finding_to_concept: human_gated`.** BD's stated
reason was *"to stop an agent inflating its own concepts."* Here it is more
direct.

> **An agent promoting its own retrieval results to ground truth is a
> self-confirming loop.** What ranked high gets cited; having been cited it becomes
> an oracle; being an oracle keeps it ranked high.
>
> **This is the same objection rt README §2 raised against the whole system** —
> *"a positive feedback loop either diverges or confirms itself. If the three axes
> feed each other, whatever bias they share gets amplified"* (`C-001`). Retrieval
> feedback is where that loop closes most tightly, and **the only damping is human
> approval.**

Promotion requires all of:

| Condition | Why |
|---|---|
| `verdict: useful` | A failure record is not an oracle |
| `cited` non-empty | A session with no citation carries no signal |
| **Reproduced under two distinct `index_sha`** | Not an accident of one index state |
| Human approval | Blocks self-confirmation |

### Fixture F9

Added to [BUILD.md](BUILD.md) §2.

| # | Claim under test | Fixture |
|---|---|---|
| **F9** | An oracle **really catches a regression** | Create one oracle, then break the profile on purpose — **the test must fail** |

> Note that F9's pass condition is that something fails. Break it and stay green
> and the oracle is an unwired checker — BD `tools/kb.py`'s recorded failure mode.

---

## 6. Decisions

| # | Decision | Value | Grounds |
|---|---|---|---|
| 1 | How `cited` is collected | **reported by the calling agent**, never inferred | Inferred, it stops being a fact and becomes an estimate |
| 2 | When the report is missing | stays `not_searched` (the default is failure) | Constraint ① |
| 3 | Keeping the raw `query` | **kept** — it is the reproduction input | Without it an oracle cannot be re-run |
| 4 | Unpublished content inside `query` | subject to the `publish-gate` | **The query itself reveals the direction.** This repo is public, so this is the first exposure path, ahead of the digest → [PLAN.md](PLAN.md) §6.1 |
| 5 | Reproductions required for promotion | **two distinct index SHAs** | One is indistinguishable from chance |

### Open

| # | Decision | Blocks |
|---|---|---|
| a | **`publish-gate` scope for `sessions/`** — hash the query · gitignore `sessions/` and commit `oracles/` only · commit as-is | Implementing this folder. **Until it is settled, session files are not committed** |
