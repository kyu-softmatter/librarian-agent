# `profiles/` — one query profile per calling agent

A `caller_profile` is a **versioned config file, not a query the LLM composes each
time.** The design comes from BD `I-053`: perspective separation is produced not
by separate stores but by *a different search query per persona* — with the
consequence that a large corpus costs nothing in context, because it is an index
and not context.

```yaml
id: ms:lens-5-photo-perturbation
prefer_kinds:   [assumed, measured, source, decision]
require_fields: [evidence, tier]          # a hit without these is dropped
boost:
  quantity_match: 3.0                     # matches a data/*.yaml field name
  gate_match:     2.5                     # G10, ...
exclude:
  reproduced: [no]                        # never raise an unreproduced value as grounds
return_always:  [falsifier, conditions, transfer_conditions]
```

## v1: a pair, not one

`ms:lens-5-photo-perturbation` and `ms:lens-4-sample-optics`.

**One profile cannot demonstrate that profiles do anything.** The acceptance
criterion is that the same question returns a different top three under each
([../BUILD.md](../BUILD.md) §4-B), and these two consume different corpora: lens 5
owns `bleach_photons` and G10, lens 4 owns G15-G19 and the captured priors on
immersion media, coverslip thickness and medium refractive index.

## The rule that keeps ranking honest

**Rank is returned, never stored in an entry.** A relevance score orders
retrieval; stored in an entry it becomes a scalar claim that "this one matters
more," which is the prohibition on `value_score` returning in new dress.
