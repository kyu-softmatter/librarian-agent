# CLAUDE.md

A librarian for three research agents: one index over `agentic-microscope`,
`Brownian-Dynamics-Agent` and `research-topic`, retrieval profiled per caller,
and custody that includes retirement.

**This file points; it does not restate.** The decisions live in
[PLAN.md](PLAN.md) §9, the acceptance criteria in [BUILD.md](BUILD.md), the
retrieval-feedback rules in [FEEDBACK.md](FEEDBACK.md), the folder shapes in
[TREE.md](TREE.md). A summary of them here would be a fourth copy going stale in
a repository that exists because of a stale copy — BD's
`knowledge/source/papers/INDEX.md`, which still says 40 entries where 43 files
sit. What is below is only what a session gets wrong without being told.

## The commands

```bash
python -m librarian.cli reindex --repo ms --repo bd --repo rt   # always all three
python -m librarian.cli search "..." --profile ms:lens-4-sample-optics
python -m librarian.cli gaps --missing-only     # which gate is BLOCKED, for want of what
python -m librarian.cli inputs <computation>    # what it needs, and which of it exists
python -m librarian.cli drift --repo ms --repo bd --repo rt
python -m librarian.cli oracles                 # run the committed regression oracles
python -m pytest                                # `-m "not integration"` needs no clones
```

**A rebuild is full, never incremental.** `reindex --repo ms` alone does not
leave the other two alone — it drops them from the index. Name all three.

## Four things that are not yours to write

| | |
|---|---|
| `cache/` | the three source repositories, read-only. **Nothing here ever writes one** (decision 9). Changes reach them as pull requests, from a clone somewhere else — not from `cache/` |
| `index/`, `map/manifest.json` | derived. Delete and rebuild; never hand-edit. `map/` holds exactly one generated file — `tests/test_map.py` enforces that, and decision 38 says why |
| `kb/08-retrieval/oracles/` | written only by `librarian promote`, which **requires a person**. An agent promoting its own retrieval results to ground truth is the loop the approval exists to damp (FEEDBACK §5). `.claude/settings.json` denies the command |
| anything under `store/` or `kb/08-retrieval/sessions/` | a record of something that happened. **Do not fabricate one to demonstrate a feature.** Write real ones through the tools, or write none |

## Five results that look like failures and are not

`searched_empty` — the corpus was searched and held nothing. Distinct from
`not_searched`, which is the absence of a record that anyone looked. Report the
first; the distinction is load-bearing.

`index_stale: true` — a repository moved since the build. A warning on a valid
answer.

`advances: false` — that evidence tier cannot advance a verdict. A literature
value never can, by rule. Report the tier rather than working around it.

`status: blocked` from `kb_supplies`, `filled: 0` from `kb_gaps` — nothing
supplies that field anywhere. The microscope returns BLOCKED by design; the
useful answer is *which input*.

**A red `integration` job in CI** — *"red means a source repo moved."* It is
`continue-on-error` for that reason. Read it, do not silence it. And **no test
in that job may skip itself**: every clone is present there by construction, so
a skip means a test did not run while the tick said it did.

## How to add an adapter

One per repository contract, named `<repo>_<source>.py` — `librarian.scan`
selects on that prefix. Register it in `adapters/__init__.py` **and** in
`CANDIDATES` in `librarian/scan.py`; the candidate list is enumerated
independently of the adapter on purpose, so a folder the adapter silently drops
is reported instead of lost.

**Read the source's declared contract first, and check it against the whole
corpus.** Two claims in PLAN.md were generalized from a single file and both
were wrong: §1.4 said BD's papers carry a `provides:` array (1 of 42 do), and
§1.4c records that BD's `design/ideas.md`, cited here six times as grounds, is
not in BD's public repository at all. rt's `ideas.md` states its own rules in a
section headed *"Rules for this document"* — including that a prefixed id like
`BD:I-050` is a citation **out** and not an item of its own.

## The one rule the whole thing rests on

**This repository originates no numbers.** Every value it returns is quoted
from a file with `repo@sha:path#locator` attached. A hit without coordinates is
not returned, and a claim that cannot be walked back to a location is not
usable — which applies to prose written here as much as to a tool's output.

For the LLM step specifically, [PLAN.md](PLAN.md) §6 Tier 2: **originating or
summarizing numbers is forbidden**, as is assigning `evidence: measured`. A
draft that needs a number it cannot cite leaves the slot empty in the target's
own placeholder form and goes to `store/inbox/` for a person — see
`store/inbox/crosswalk/` for the worked example.
