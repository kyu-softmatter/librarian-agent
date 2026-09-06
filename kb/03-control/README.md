# `kb/03-control/` — Instrument control stack

MicroManager `.cfg` behaviour, the piezo command set, LUNF/DAQ wiring,
channel definitions — what issues commands to the hardware.

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

**A card is:** (control stack x task) — e.g. `micromanager-dualcam--two-colour-acquisition.md`

A card owns the **convention and the routing**; it does not own values. Values sit
in `evidence/` with a tier. Without that split, "what value was used here" has no
source attached to it.

## Boundary

**"Software" names three different things** ([../../TREE.md](../../TREE.md) §2-C).
Only the instrument control stack lives here.

| Not this | Where |
|---|---|
| MS's own agent code (gate modules, G1-G32) | `map/04-agents/ms/` — derived |
| The analysis code (`D:\codes`, read by lens 6) | deferred to v2 |

**Does not belong here.** Agent code, or analysis code. See the table above.

## The tier is in the path as well as the field

`evidence: assumed` under `evidence/measured/` is a contradiction, and the index
reports it ([../../PLAN.md](../../PLAN.md) §4.3). The duplication is deliberate: a
frontmatter line gets written wrong and goes unnoticed, and a path does not. BD
filed `T = 300 K` as measured when it was a choice, and it propagated -4% to -14%
into every downstream `tau_B`.
