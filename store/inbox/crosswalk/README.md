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

## The sources, and what they turned out to be

The operator supplied two DOIs and then both PDFs. **They are both for this one
entry**, which is not what this README guessed:

| DOI | | TRITC lifetime |
|---|---|---|
| `10.1002/jemt.22349` | Nanguneri et al., *Microsc Res Tech* 77(7):510-516, 2014 | **2.2 ns free dye in PBS**, 2.3 ns phalloidin conjugate, 1.7 ns with 30 mM tryptophan |
| `10.1177/43.7.7608524` | Brismar, Trepte & Ulfhake, *J Histochem Cytochem* 43(7):699-707, 1995 | 1.58 ns free dye **in ethanol** (SD 10 ps), 3.32 + 1.4 ns IgG conjugate |

**The 2014 paper was guessed here to be about `Phal647`** — its title is about
phalloidin-fluorophore conjugates — and it reports no lifetime for Alexa Fluor
647 at all. What it does report is TRITC's, **in PBS**, which is the one
condition the 1995 paper lacked: that paper dissolved free TRITC in ethanol
while putting its other three dyes in distilled water.

So the entry files **2.2 ns**, cites the 2014 paper for it, and keeps 1.58 ns as
an independent cross-check in a different solvent — two instruments, 572 and
575 nm, landing 1.4x apart. `confidence: low` stands: they agree in magnitude,
not to a figure.

**And the two disagree about what conjugation does**, which is worth more than
either number. Brismar's IgG conjugate rises 1.74 ns and turns
double-exponential; Nanguneri's phalloidin conjugate stays flat and the
quenching is attributed to a static dye-tryptophan complex. "Conjugated" is not
one condition.

## Why the value was filed after all, and what is still open

An earlier version of this README said the value was the operator's to supply
because the paper was closed access. With the PDFs in hand it was read from
**Table 1** and from the **Fluorescence Lifetime** section, so the number is
quoted from the source rather than recalled — which is what §6's prohibition is
about.

`filed_by` is still unfilled. It attests that a person checked the citation
against the paper, and that signature is not this repository's to give.

## Two defects found while doing it

**`photo/cli.py` is broken and has been since G10's removal.** Every
invocation, including `--help`, raises `TypeError`: commit `3695b22` deleted the
body of the `--bleach-photons` argument and left `c.add_argument(\n    )`
behind. Removing the empty call revives the CLI, and that is how the
before/after numbers in the entry were produced. **A separate pull request, and
it blocks this one** — the entry's `## What it supplies` section cannot be
verified by a reader without it.

**The claim that a factor of two in tau flips G20's verdict was wrong.** It was
derived at an arbitrary excitation rate, not this instrument's. At the measured
`power_at_sample_mw` for the band that excites TRITC, all four candidate values
pass with the saturation margin clamped at its ceiling, 241x or more below the
strictest boundary. Corrected in the entry, and stated there as the reason the
remaining condition mismatches are tolerable.

## What this is not

**Not the BD crosswalk.** [../../../PLAN.md](../../../PLAN.md) §1.4 planned the
first literature entries as a 1→N decomposition of BD's paper distillations, and
BD holds **no fluorophore data at all** — its 42 papers are colloid and
active-matter physics. That gap and this entry are two different tasks, which
§1.4 had treated as one; it is corrected there.
