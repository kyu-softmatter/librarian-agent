---
id: lifetime-ns-tritc
quantity: "data/fluorophores.yaml > TRITC > lifetime_ns"
question: "What fluorescence lifetime should be assumed for TRITC in aqueous
  buffer, so that G20 can say whether emission is still linear in power, and
  under what conditions was the published value obtained"
source: literature
citation: "Brismar H, Trepte O, Ulfhake B. Spectra and fluorescence lifetimes of
  lissamine rhodamine, tetramethylrhodamine isothiocyanate, texas red, and
  cyanine 3.18 fluorophores: influences of some environmental factors recorded
  with a confocal laser scanning microscope. J Histochem Cytochem
  43(7):699-707, 1995."
doi: "10.1177/43.7.7608524"
filed_by: <initials>
date: <YYYY-MM-DD>
confidence: low
evidence: assumed
gate: G20
scope: "TRITC excited in the 547 nm absorption band, in aqueous buffer, on the
  two sources whose power at the sample plane is measured: `Spectra > Green`
  (555 nm, FWHM 28) and `LUN-F-XL > 561` (561 nm, FWHM 1), at 4x / 10x / 20x.
  Not for the ATPS phases or any sucrose-loaded buffer until the medium's own
  properties are on record — see [[sample-medium-refractive-index]].
  **The instrument class matches**, which is unusual for a literature value
  here: these lifetimes were recorded on a confocal laser scanning microscope
  and this instrument's CSU-W1 is one. That narrows the transfer gap; it does
  not close it — a 1995 confocal is not this confocal."
applies_to_systems: [current-spectra, current-laser]
measured_on: "Confocal laser scanning microscope. **This paper does not report
  one lifetime — it reports how the lifetime moves**, and its own abstract names
  the three factors it varies: *pH changes, IgG conjugation, and tissue
  embedding procedures all influenced fluorescence characteristics.* So state
  which row the filed value is taken from: <pH, conjugated to IgG or free dye,
  embedded or in buffer, and the temperature if the paper gives one>. A value
  copied without naming its condition is not this paper's number."
review_after: <YYYY-MM-DD>
supersedes: null
superseded_by_measurement: null
---

> **⚠ This is a scaffold, not an entry, and it is in `store/inbox/` for that
> reason.** Every section below is filled from this repository's index, at
> locators. **Four things are deliberately empty** — the value in `## Verdict`,
> `citation`, `doi`, `filed_by` — because supplying them is reading a paper and
> transcribing a number, which is what `PLAN.md` §6 forbids of this
> repository's LLM step and what `librarian`'s first invariant forbids of the
> server. The placeholders use the `<...>` form `_template.md` itself uses, so
> MS's own adapter reads them as absent rather than as values.
>
> **Nothing leaves `store/inbox/` without human approval** (`store/README.md`).
> Filling the four and filing it is the operator's act, and it becomes a pull
> request against `agentic-microscope` — never a direct write.

## Verdict

**<value> ns** (<uncertainty, or the range across the conditions the paper
reports>), **at <the condition: pH, conjugated or free, embedded or in buffer>**.

State the number first, and state **which of the paper's rows it is**. This
paper reports the lifetime *as a function of* pH, IgG conjugation and embedding,
so *"TRITC is <value> ns"* is not something it says — and the gate's verdict
turns on a factor of two in tau, which is inside the range those factors move it
across.

If the decay is multi-exponential, say which component and its amplitude
fraction, and give the intensity-weighted average if that is what is being
filed — `photo/dose.py` takes a single scalar
`lifetime_ns` and computes `k_ex tau / (1 + k_ex tau)`, so a two-component decay
collapsed silently into one number is a transfer condition, not a formatting
choice.

## What it supplies

- **Field:** `data/fluorophores.yaml > TRITC > lifetime_ns` (currently `null`;
  6 of 17 dyes in the registry are missing it)
- **Gate:** `G20` — saturation / triplet shelving — in `photo/checks.py`,
  threshold `excited_state_fraction_max: 0.1`
- **Before this entry:** `photo/gate.py` `_missing_inputs()` emits
  `missing.lifetime` at severity `fail` — *"The dye has no fluorescence lifetime
  on record, so the saturation check (G20) cannot tell whether emission is still
  linear in power"*, with the action *"Add lifetime_ns to the dye's entry in
  data/fluorophores.yaml."* The lens returns **BLOCKED**, so no margin, no
  bottleneck and no difficulty grade for any TRITC setting.
- **After:** G20 computes two things it cannot compute now.
  `photo.dose.excited_state_fraction(k_ex, tau) = k_ex*tau / (1 + k_ex*tau)`
  becomes a number to compare against 0.1, and
  `photo.dose.saturation_irradiance_w_cm2(ext_coeff, tau, wavelength)` becomes
  available — **which is why TRITC and not one of the other five.** TRITC
  already carries `ext_coeff_M1cm1: 85000`; `SYTO61` and `DragonGreen` carry no
  extinction coefficient, so supplying their lifetime alone would move them
  from one missing input to another, and `DEX647`, `SA647` and `Phal647` share
  one nominal 270000 across three different conjugates.

## Transfer conditions

What has to hold for this number to apply to this instrument:

1. **The condition the value was taken at is the condition here.** Not a
   generic caution: this paper's own finding is that pH, IgG conjugation and
   embedding each move the lifetime, and its conclusion is that *"changes in
   spectra and fluorescence lifetimes may be a useful tool to gain information
   about the chemical environment of the fluorophores"* — the quantity is
   being proposed as an environment probe. One row of it applies here only
   where the environment matches.
2. **The medium is ordinary aqueous buffer.** The project's own sample systems
   are the exception rather than the rule: `kb/expertise/sample-medium-refractive-index`
   lists ATPS (dextran/PEG), sucrose and glycerol as cases where a gate must
   refuse rather than substitute a default. A lifetime taken in water does not
   transfer into 55 % sucrose, and the newest plan
   (`kb/plans/2026-09-15-drag-calibration-stiffness-vs-size`) is in sucrose.
3. **The excitation stays in the band the paper used**, and within the linear
   regime it was measured in. G20 exists precisely to find the edge of that
   regime, so a value measured at an irradiance far from this instrument's is
   being extrapolated by the gate that is checking for extrapolation.
4. **The conjugate matches, or the difference is stated.** `TRITC` in this
   registry is a name covering free dye and any TRITC-labelled conjugate, and
   `aliases: [TRITC555, tritc]` does not distinguish them — while IgG
   conjugation is one of the three factors this paper measured as significant.
   The registry's single name spans values the source says differ.

What is known **not** to hold:

1. **The registry's TRITC row is a catalogue nominal, `verified: false`.** Its
   own header says so of every row: *"The values below are all catalog nominal
   values ... parametric band(peak+FWHM) gets the peak position right but the
   wings wrong."* So the `ext_coeff_M1cm1: 85000` that this lifetime will be
   combined with in `saturation_irradiance_w_cm2` is itself unverified, and the
   product of two nominals is not better than either.
2. **No spectra file.** TRITC has no `curves:` entry, so the gate computes from
   peak + FWHM and, by the registry's own rule, downgrades confidence to low.
3. **`photostability: medium` is a grade, not a number.** Triplet shelving is
   explicitly not modelled — `photo/checks.py` says the 0.1 threshold is
   "generous" for that reason — so real saturation arrives earlier than G20 will
   report, in a direction the margin does not show.

## Why this does not advance a verdict

`evidence: assumed`, so `advances` stays `NO` regardless of the margin
([04 §1](../../docs/04-decision-engine.md)). This entry lets `G20` compute
instead of refuse; it does not claim anyone measured TRITC's lifetime on this
instrument, in this buffer, under this illumination. The replacement is the
saturation power series named in §1 of Falsification conditions below.

## Falsification conditions

1. **A local measurement of the saturation point, which this instrument can
   actually do.** A direct lifetime needs time-resolved detection this setup
   does not have, so the falsifier is the quantity G20 is really about:
   acquire an emission-versus-power series on a fixed TRITC field and find the
   irradiance at which emission departs from linear. `k_ex*tau = 1` at
   excited-state fraction 0.5, so the departure fixes `tau` given the
   irradiance — and the irradiance is available, because
   `data/light_sources.yaml` now carries **measured** `power_at_sample_mw` for
   both usable bands: `Spectra > Green` at 17.5 / 16.7 / 15.3 mW and
   `LUN-F-XL > 561` at 6.9 / 6.7 / 6.5 mW, for 4x / 10x / 20x. On arrival: move
   the value to `kb/calibrations/`, set `superseded_by_measurement:` above, and
   G20 becomes able to advance.
2. **A second published value, at a stated condition, disagreeing by more than
   a factor that changes
   G20's verdict.** The threshold that matters is not statistical: the gate
   compares `k_ex*tau/(1 + k_ex*tau)` against **0.1**, which puts the boundary
   at `k_ex*tau = 1/9`. So a disagreement matters when it moves `k_ex*tau`
   across `1/9` at this instrument's irradiance — state that comparison, not a
   percentage.
3. **Transfer condition 1 turning out to be false** — the run that needs this
   is in sucrose, and a lifetime measured in water may not survive the medium
   the experiment actually uses.

## Related

- `photo/checks.py` — G20, and the `excited_state_fraction_max: 0.1` threshold
- `photo/dose.py` — `excited_state_fraction`, `saturation_irradiance_w_cm2`
- `photo/gate.py` — `_missing_inputs()`, which emits `missing.lifetime` today
- `data/fluorophores.yaml` — the registry field, and the header stating every
  row is a catalogue nominal
- `data/light_sources.yaml` — the measured `power_at_sample_mw` that makes
  falsification condition 1 available
- `kb/expertise/sample-medium-refractive-index.md` — why the sucrose and ATPS
  media are excluded from `scope`
- `kb/decisions/2026-09-09-g10-photobleaching-removed.md` — G10 was the live
  case `kb/literature/README.md` still describes; G20 is the live case now

---

> **What is still missing, and why it is not here.** The citation and DOI above
> were read from **Crossref**, the registry of record, rather than recalled.
> The **value** was not: the paper is closed access (OpenAlex `oa_status:
> closed`; the publisher returns 403) and its abstract states that lifetimes
> were recorded without giving them. So the number, the condition it is taken
> at, and `filed_by` are the operator's to supply from the paper itself.
>
> A number obtained any other way would carry exactly the defect BD recorded
> against its own `mason-weitz-1995`: `verified: false  # bibliographic info
> from memory; confirm before citing`. This entry would carry it **without the
> flag**, in a folder whose whole purpose is that a published value can be used
> without being mistaken for something measured here.
