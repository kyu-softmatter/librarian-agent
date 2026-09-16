# `store/inbox/crosswalk/` — proposed entries, awaiting a person

A file here is an **MS-shaped draft this repository produced and cannot
finish.** It leaves in one direction only: the operator fills what is missing,
files it in the target repository, and it arrives there as a **pull request**.
Nothing here is canonical and nothing here is evidence.

**What this repository may and may not put in a draft.** It may fill any section
from what is already indexed, at a locator — a gate's threshold, the finding a
gate emits today, a registry row, a measured power. It may **not** supply the
number the entry exists for, or its citation: that is reading a paper and
transcribing a value, which [../../../PLAN.md](../../../PLAN.md) §6 forbids of
the LLM step (*"Forbidden in Tier 2: originating or summarizing numbers"*) and
which the server's first invariant forbids outright.

So a draft is deliberately incomplete in a specific way, and the gap is marked
in the form the target's own template uses — `<...>` — which MS's adapter reads
as absent rather than as a value.

| Draft | For | Missing |
|---|---|---|
| [`lifetime-ns-tritc.md`](lifetime-ns-tritc.md) | `ms:kb/literature/lifetime-ns-tritc.md` — the folder's **first** entry | the **value** and the condition it is taken at · `filed_by` · `date` · `review_after` |

## The source, and why the citation is filled and the value is not

The operator supplied **`10.1177/43.7.7608524`** — Brismar, Trepte & Ulfhake,
*J Histochem Cytochem* 43(7):699-707, 1995, *"Spectra and fluorescence lifetimes
of lissamine rhodamine, tetramethylrhodamine isothiocyanate, texas red, and
cyanine 3.18 fluorophores."* **TRITC is tetramethylrhodamine isothiocyanate**,
so this paper measures the quantity directly, and it does so **on a confocal
laser scanning microscope** — the same instrument class as this one's CSU-W1,
which is unusually close for a literature value.

**The citation and DOI are filled because they came from Crossref**, the
registry of record. The value is not, because the paper is closed access
(OpenAlex `oa_status: closed`; the publisher returns 403) and its abstract
states that lifetimes were recorded without giving them.

**And the paper does not report one lifetime.** Its abstract's own finding is
that *"pH changes, IgG conjugation, and tissue embedding procedures all
influenced fluorescence characteristics"*, and its conclusion proposes the
lifetime as a probe *of* the chemical environment. So filing it means choosing a
row and saying which — which matters here rather than being bookkeeping: G20's
verdict turns on a factor of two in tau, and that is inside the range those
three factors move it across.

## The second DOI is a different entry, and probably not this folder

`10.1002/jemt.22349` — Nanguneri et al., *Microsc Res Tech* 77(7):510-516,
2014, on **tryptophan-quenching-induced photoswitching of phalloidin-fluorophore
conjugates**. That bears on `Phal647`, another of the five dyes missing
`lifetime_ns`, but its subject is photoswitching in aqueous buffer rather than a
lifetime.

MS's own rule decides where it goes: *"If no gate consumes a number from it, it
is not knowledge this system can act on. Method papers that shape a judgment
belong in `kb/expertise/` as a captured prior, with the paper cited inside."*
Unless it reports a number `data/fluorophores.yaml` carries, it is an expertise
entry, not a literature one.

## Why TRITC, and why `lifetime_ns`

MS's template makes an entry conditional on changing what a gate can do —
*"an entry that does not change what a gate can do is not worth filing."* MS has
exactly two registry gaps, and only one of them is a published number:
`data/fluorophores.yaml > lifetime_ns`, missing for 6 of 17 dyes, consumed by
**G20**. Without it `photo/gate.py` emits `missing.lifetime` and the lens
returns BLOCKED.

Of the six, **TRITC is the only one where the lifetime is the last missing
input.** `photo.dose.saturation_irradiance_w_cm2` needs the extinction
coefficient as well; `SYTO61` and `DragonGreen` carry none, and `DEX647`,
`SA647` and `Phal647` share one nominal `270000` across three different
conjugates. TRITC carries `ext_coeff_M1cm1: 85000` of its own.

## What this is not

**Not the BD crosswalk.** [../../../PLAN.md](../../../PLAN.md) §1.4 planned the
first literature entries as a 1→N decomposition of BD's paper distillations, and
BD holds **no fluorophore data at all** — its 42 papers are colloid and
active-matter physics. That gap and this entry are two different tasks, which
§1.4 had treated as one; it is corrected there.
