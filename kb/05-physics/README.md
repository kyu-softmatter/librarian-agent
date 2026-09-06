# `kb/05-physics/` — Physical phenomena

> **Empty until v2.** This is BD's domain and there is no adapter for it yet.

Phenomena and relations that hold regardless of which engine or
instrument is used. Dimensionless groups, phase behaviour, constitutive relations.

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

**A card is:** (phenomenon x regime) — e.g. `microrheology--linear-viscoelastic.md`

A card owns the **convention and the routing**; it does not own values. Values sit
in `evidence/` with a tier. Without that split, "what value was used here" has no
source attached to it.

## Boundary

**The boundary against `06-simulation` is the engine-swap test:**

> Swap the engine from HOOMD to LAMMPS. Does the entry change?
> **No -> here.** Yes -> `06-simulation`.

GSER does not change, so it belongs here. The `dt` gate does, so it does not.

**Does not belong here.** Anything that changes when the engine changes.

## The tier is in the path as well as the field

`evidence: assumed` under `evidence/measured/` is a contradiction, and the index
reports it ([../../PLAN.md](../../PLAN.md) §4.3). The duplication is deliberate: a
frontmatter line gets written wrong and goes unnoticed, and a path does not. BD
filed `T = 300 K` as measured when it was a choice, and it propagated -4% to -14%
into every downstream `tau_B`.
