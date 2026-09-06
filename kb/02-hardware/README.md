# `kb/02-hardware/` — Microscope hardware

What is physically in place: objectives, immersion media, cameras,
light sources, filters, stages, and what has been measured about them.

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

**A card is:** (instrument configuration x mode) — e.g. `current-laser--optical-tweezers.md`

A card owns the **convention and the routing**; it does not own values. Values sit
in `evidence/` with a tier. Without that split, "what value was used here" has no
source attached to it.

## Boundary

A **system dossier** is a card: one instrument configuration per file, with
machine-readable frontmatter and a prose body (MS `docs/02` §3).

**Does not belong here.** How the instrument is commanded. That is `03-control`.

## The tier is in the path as well as the field

`evidence: assumed` under `evidence/measured/` is a contradiction, and the index
reports it ([../../PLAN.md](../../PLAN.md) §4.3). The duplication is deliberate: a
frontmatter line gets written wrong and goes unnoticed, and a path does not. BD
filed `T = 300 K` as measured when it was a choice, and it propagated -4% to -14%
into every downstream `tau_B`.
