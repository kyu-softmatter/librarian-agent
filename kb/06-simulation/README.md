# `kb/06-simulation/` — Simulation

> **Empty until v2.** This is BD's domain and there is no adapter for it yet.

How a system is actually run: reference scales, the non-dimensionalization
convention, which gates apply, benchmarks, integrator and RNG choices.

## Shape

Every subject folder has the same five slots, because things here are verified
differently rather than being about different topics (BD `docs/03` §2: *"six
kinds, **because they are verified differently**"*).

```
cards/                the canonical unit — one (subject x purpose) pair per file
evidence/measured/    measured here.  evidence: measured  -> may advance a verdict
evidence/assumed/     literature or estimate.  evidence: assumed  -> may not
findings/             Q->A with citations.  includes dead-end-<slug>.md
questions/            unanswered. Closed by status, never deleted
```

**A card is:** (system x purpose dynamics) — **BD's convention, unchanged**

A card owns the **convention and the routing**; it does not own values. Values sit
in `evidence/` with a tier. Without that split, "what value was used here" has no
source attached to it.

## Boundary

**BD's card convention is inherited verbatim**, because BD demonstrated by
measurement that the convention is not fixed by the system alone — within one lab
the reference time split three ways across (system, purpose dynamics) pairs
(`knowledge/wiki/CLAUDE.md`).

Its rule carries over: **on meeting a pair with no card, do not improvise the
non-dimensionalization.** Start a card at `status: draft` instead.

**Does not belong here.** A phenomenon that survives an engine swap. That is `05-physics`.

## The tier is in the path as well as the field

`evidence: assumed` under `evidence/measured/` is a contradiction, and the index
reports it ([../../PLAN.md](../../PLAN.md) §4.3). The duplication is deliberate: a
frontmatter line gets written wrong and goes unnoticed, and a path does not. BD
filed `T = 300 K` as measured when it was a choice, and it propagated -4% to -14%
into every downstream `tau_B`.
