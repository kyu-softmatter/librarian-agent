# `profiles/` — one query profile per caller

A `caller_profile` is a **versioned config file, not a query the LLM composes each
time.** The design comes from BD `I-053`: perspective separation is produced not
by separate stores but by *a different search query per persona* — with the
consequence that a large corpus costs nothing in context, because it is an index
and not context.

```yaml
id: ms:lens-5-photo-perturbation
lens: 5

kind_weight:                     # a weight, never a filter
  calibration:     2.0           #   measured here; outranks anything published
  literature_form: 1.8           #   the tier built to be replaced by a calibration
  registry:        1.6           #   the field a gate reads at runtime
  agent:           0.5

boost:
  gate:  [G10, G20, G21, G22]              # from photo/checks.py docstrings
  field: [bleach_photons, lifetime_ns]     # from setup.<field> in photo/*.py
  path_prefix: [data/fluorophores.yaml, kb/literature]

demote:
  reproduced: {"no": 0.7}                  # demoted, never excluded

return_always: [evidence, tier, has_falsifier, conditions, review_after]
```

## Two filters that were drafted here and removed

Both looked like rigour and both removed the answer.

| Drafted | What it did on the real corpus | Now |
|---|---|---|
| `require_fields: [evidence, tier]` — a hit without these is dropped | **495 of 544 documents carry no evidence tier**, including every `docs/` section. Asked what G10 checks, the profile dropped the answer | `return_always`: the tier is **carried**. Carrying it is what stops a caller mistaking `assumed` for `measured`; dropping untiered documents was never the mechanism. A hard filter is opt-in per query (`require`), not per profile |
| `exclude: reproduced: [no]` | Most registry entries state `verified: false` deliberately — the headers say the values are catalog nominals whose wings are wrong. `data/fluorophores.yaml > AlexaFluor488` is exactly what lens 5 needs | `demote`: BD's rule is not to raise an unreproduced value as **grounds**. It is still the right pointer |

## Scoring

```
score = (-bm25) x kind_weight x (1 + 0.5 per boost class hit) x demote
```

`bm25` is negative and lower is better, so it is flipped; boost classes are
`gate`, `field` and `path_prefix`, each contributing once. **Ties break on
`uid`**, so the same index answers the same question in the same order — an
oracle over an unstable order tests nothing.

Unranked queries (all terms shorter than three characters, so `GLOB` only) score
on `kind_weight` and boosts alone.

## v1: a pair, not one

`ms:lens-5-photo-perturbation` and `ms:lens-4-sample-optics`.

**One profile cannot demonstrate that profiles do anything.** The acceptance
criterion is that the same question returns a different top three under each
([../BUILD.md](../BUILD.md) §4-B), and these two consume different corpora: lens 5
owns `bleach_photons` and G10, lens 4 owns G15-G19 and the captured priors on
immersion media, coverslip thickness and medium refractive index.

**Verified disjoint.** Asked *"what limits how long I can image this dye"* over
544 real documents:

```
lens 5  ->  kb/literature/README.md  (three sections: the tier rule, what
                                      belongs, why transfer is the difficulty)
lens 4  ->  kb/expertise/            (oil-objective clipping, medium refractive
                                      index, coverslip thickness)
```

No overlap in the top three. The gate and field lists are read off the
repository — `photo/checks.py` and `sample/checks.py` docstrings for the gates,
`setup.<field>` occurrences for the fields — so a profile does not drift from the
code it is written against without that showing up.

## People get profiles too — by role, never by person

Planned for v2 → [../PLAN.md](../PLAN.md) §3.5.

A person reaching the NAS server asks in their own words and has no lens. What
they get instead is a `human:*` profile — the same file form, the same weights,
applied the same way server-side — plus a `purpose` argument on the query,
because the same person asks for different reasons on different days.

**Keyed by role and purpose, never by person.** Two reasons, and neither is
tidiness:

- Profiles should multiply with **kinds of question**, not with people. A file
  per person goes stale the day that person changes what they work on, and
  nothing notices — the stale-table problem this repository exists to catch.
- A `person:<name>` profile records **who was looking for what** in a public
  repository. That is the disclosure `publish-gate` exists to stop
  ([../PLAN.md](../PLAN.md) §6.1), except committed rather than logged.

**And a declared role is a claim, not a fact.** Among three agents on one machine
a wrong `caller_profile` is a bug in a config file. On a NAS several people can
reach, it asserts *who is asking*, nothing checks it, and what comes back is
plausible, correctly cited, and **not what that person needed** — which the
answer does not show. Whether the service verifies the claim is open
([../PLAN.md](../PLAN.md) §9, decision (l)).

## The rule that keeps ranking honest

**Rank is returned, never stored in an entry.** A relevance score orders
retrieval; stored in an entry it becomes a scalar claim that "this one matters
more," which is the prohibition on `value_score` returning in new dress.
