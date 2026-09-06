# `kb/01-materials/` — Materials and sample systems

Knowledge attached to **what is being imaged**. Optical properties of a
sample, labelling, characteristic scales, known pitfalls.

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

**A card is:** (sample system x observed dynamics) — e.g. `atps-peg-dextran--interfacial-relaxation.md`

A card owns the **convention and the routing**; it does not own values. Values sit
in `evidence/` with a tier. Without that split, "what value was used here" has no
source attached to it.

## Boundary

**Why this is separate from `02-hardware`: lifetime, not subject.**
MS `docs/02-knowledge-base.md` §8: *"Knowledge attached to what is being imaged,
not to a system. **It survives hardware changes.**"* Swap the objective and
`02-hardware` changes while this folder does not.

**Does not belong here.** An instrument value. That is `02-hardware`.

## The tier is in the path as well as the field

`evidence: assumed` under `evidence/measured/` is a contradiction, and the index
reports it ([../../PLAN.md](../../PLAN.md) §4.3). The duplication is deliberate: a
frontmatter line gets written wrong and goes unnoticed, and a path does not. BD
filed `T = 300 K` as measured when it was a choice, and it propagated -4% to -14%
into every downstream `tau_B`.
