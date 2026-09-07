# Build and verification — what must pass before any data moves

Drafted 2026-09-06 · status `draft` · this is Step 0 of
[MIGRATION.md](MIGRATION.md)

**Decision: build the structure in full, verify it works separately, and migrate
only then.** **v1 is the microscope agent only** → [PLAN.md](PLAN.md) §0.

That order is not a preference. rt `design/kb-schema.md` §0 already wrote the
grounds:

> *"No KB entries are created. Only their shape is fixed. … **That order looks
> backwards on purpose.** BD's `I-075`/`I-076` already diagnosed the two ways a KB
> dies. **Filling before the form is fixed means throwing away what was filled
> when the form changes.**"*

rt README §4 Phase 2 fixes the same thing as *"interlocks (**before** any KB
content)."* **This decision agrees with all three repositories.**

---

## 1. The problem — an empty KB cannot be verified

A retrieval system works when a query returns the right thing. With `kb/` empty
every query returns nothing, and that is indistinguishable from three other
states.

| Actual state | Returns |
|---|---|
| The corpus is empty | 0 |
| The index was never attached | 0 |
| The tokenizer cannot segment the language | 0 |
| The adapter failed to read the frontmatter | 0 |

**Four states, one face.** And it is the same shape as an accident BD recorded:
`tools/kb.py` pointed at a renamed path and *"simply reported 'run-less knowledge
0' for 126 existing entries. A silently empty read is the same failure mode as an
unwired checker."*

**→ Resolution: a fixture corpus.** Verify against **copies** of real entries.
A copy is not a migration.

| | Fixtures (now) | Migration (later) |
|---|---|---|
| Originals | **untouched** | deleted |
| To undo | delete `fixtures/` | requires the Step 4 proof |
| Location | `fixtures/` — separate from `kb/` | `kb/` |
| Count | 9 | 264 |

> **Fixtures are discarded when migration begins.** They are not moved into
> `kb/` — leaving them would put the same entry in two places, which is the state
> this project exists to remove.

---

## 2. Nine fixtures — one claim each

One fixture per claim made in the design documents. A claim with no fixture is a
claim that was never checked.

| # | Claim under test | Fixture | v1 |
|---|---|---|---|
| **F1** | The evidence tier lives in **both path and field**, and a disagreement is caught ([TREE.md](TREE.md) §4) | MS `kb/calibrations/camera-readout.yaml` (measured) + a copy deliberately mis-filed as `evidence: assumed` under `measured/` | ✅ |
| **F2** | BD paper → MS quantity decomposition is **1→N** ([PLAN.md](PLAN.md) §1.4) | BD `1995-mason-weitz-gser-microrheology.md` — `provides: [gser-formula, msd-to-moduli, newtonian-limit-check]` → 3 files | v2 |
| **F3** | The `05`/`06` boundary is settled by the **engine-swap test** ([TREE.md](TREE.md) §2-B) | BD `wiki/concepts/water-298k.md` (→05) + one `wiki/systems/` card (→06) | v2 |
| **F4** | `has_falsifier = 0` produces an **entry-defect report** | MS `kb/expertise/` — 5 of 6 entries carry `## Falsification conditions`; `oil-objective-trapping-in-water.md` does not | ✅ |
| **F5** | A challenge **routes by falsifier type** | The same oil-objective entry — rt README §2.2 records it as *"a challenge that was upheld"* | ✅ |
| **F6** | Retrieval works over a mixed Korean/English corpus | One BD paper distillation body (Korean) inserted **as a tokenizer test only**, with no BD adapter | ✅ |
| **F7** | Decay of a derived artefact is **detected automatically** ([PLAN.md](PLAN.md) §1.2) | BD `source/papers/INDEX.md` — missing generator, 40 vs 42. A file-level check, so no adapter is needed | ✅ |
| **F8** | `caller_profile` **actually changes results** ([PLAN.md](PLAN.md) §5.1) | The same question under `ms:lens-5-photo-perturbation` and `ms:lens-4-sample-optics` | ✅ |
| **F9** | An oracle **really catches a regression** ([FEEDBACK.md](FEEDBACK.md) §5) | Build one oracle, then break the profile on purpose — **the test must fail** | ✅ |

**F4 and F5 share a file deliberately, and running it corrected the claim made
here.** The fixture was written expecting
`kb/expertise/oil-objective-trapping-in-water.md` to *carry* a falsifier. It does
not — it has `evidence: measured`, `review_after: 2027-08-18`, `supersedes: null`
and three sections, none of them a falsification condition, while five of the six
entries beside it have one.

**That makes the specimen sharper than intended.** rt README §2.2 holds this
entry up as *"a challenge that was upheld"* — the model case for the whole
retirement mechanism — and by `kb-schema.md` §4.7 the entry itself **cannot be
challenged**, because an entry with no falsifier has nothing to cite. The
exemplar is exempt from the rule it exemplifies. That is a defect in the entry
rather than a gap in the mechanism, which is exactly what the check is for.

**F6 is kept in v1 although BD is not adapted until v2.** The tokenizer is chosen
in v1 (§3) and fixed at table-creation time, so the choice has to be verified
while it is being made.

> **F9's pass condition is that something fails.** Break it and stay green and the
> oracle is an unwired checker — BD's recorded failure mode again.

---

## 3. Decided before the schema — the tokenizer

**This must be settled before `CREATE VIRTUAL TABLE`.** An FTS5 tokenizer is fixed
at creation; changing it later means a full re-index.

Measured on this machine, SQLite 3.45.3, over one body:

```
body: "GSER 로 프로브 입자의 MSD 하나만으로 매질의 복소점탄성률을 뽑는 관계식이다.
       무차원화 규약은 master_plan §5 를 따른다. 확산계수 D 와 점도 eta, 온도 300 K, NA 1.45."
```

| query | chars | in the body as | `unicode61` MATCH | `trigram` MATCH | `LIKE '%q%'` |
|---|---|---|---|---|---|
| `무차원화` | 4 | a standalone token | 1 | 1 | 1 |
| `무차원` | 3 | inside `무차원화` | **0** | 1 | 1 |
| `점탄성` | 3 | inside `복소점탄성률을` | **0** | 1 | 1 |
| `GSER` | 4 | a standalone token | 1 | 1 | 1 |
| `확산` | 2 | inside `확산계수` | **0** | **0** | 1 |
| `점도` | 2 | a standalone token | 1 | **0** | 1 |
| `NA` | 2 | a standalone token | 1 | **0** | 1 |

Three things fall out of that table.

**① The default tokenizer returns 0 on Korean rather than an error.** `unicode61`
splits on whitespace, so a query that is a *substring* of a Korean token misses —
and Korean is agglutinative, so substrings are the normal case. BD's corpus is
Korean prose throughout: the paper distillations, the `entries/` claims,
`wiki/CLAUDE.md`. §1's fourth row is not hypothetical.

**② `trigram` fixes that and opens a hole at two characters.** FTS5's trigram
tokenizer cannot form a trigram from a two-character query, so `확산`, `점도` and
`NA` all return nothing. **`NA` is the important one** — this is not a Korean
problem but a two-character problem, and numerical aperture is among the
most-used terms in MS's domain.

**③ Neither tokenizer wins outright.** `unicode61` finds `점도` and `NA` because
they happen to be standalone tokens, and misses every Korean substring; `trigram`
is the reverse. Choosing one and stopping leaves a gap either way.

### The resolution, measured

The `LIKE` column has no zeros — and FTS5's trigram index is built precisely to
accelerate `LIKE` and `GLOB`. So:

```
one trigram table + branch on query length
  >=3 chars  ->  MATCH        (bm25 ranking available, terms OR-combined)
  <=2 chars  ->  GLOB '*q*'   (exact, case-sensitive, no ranking)
```

**No hole.** Cost: index size `unicode61` 124 KiB -> `trigram` 196 KiB for the
same 500 bodies — about **1.6x**, negligible at this corpus size.

**`GLOB`, not `LIKE` — corrected while building.** SQLite's `LIKE` is
case-insensitive for ASCII, so on the real 544-document corpus `body LIKE
'%NA%'` matched **349 documents** — every `internal`, `analysis` and `nothing` in
it. `body GLOB '*NA*'` matches **65**. For a two-character technical term case
is the signal: `NA` is the numerical aperture and `na` is a syllable. The table
above is unchanged by this; only the operator is.

**Terms are OR-combined, also corrected while building.** FTS5 defaults to AND,
and under a trigram tokenizer that requires every word of a question to appear
as a substring: *"what limits how long I can image this dye"* returned **one**
document out of 544. bm25 already favours a document matching more of the query,
so OR ranks instead of refusing. Single characters are dropped — the `I` in that
question matches almost everything and buys nothing.

> **A morphological analyzer (mecab-ko and similar) is not used.** It adds an
> external dependency, and if its output shifts with a version then **the same
> query returns different results.** Because the presence of a result is what a
> verdict turns on (BD `I-052`), reproducibility outranks ranking quality.

---

## 4. Acceptance criteria — the definition of "works"

Left to judgement, "it works well" is itself prose used as state, which
constraint ④ forbids. Migration starts when all of the following pass.

### A · Structure (must pass with no fixtures at all)

| Check | Pass condition |
|---|---|
| Subject folder shape | The five subject folders (`01` `02` `03` `05` `06`) share the same five slots — `cards` · `evidence/{measured,assumed}` · `findings` · `questions`. `00-decisions`, `07-sources` and `08-retrieval` declare their own shape and no cards ([TREE.md](TREE.md) §4) |
| Schema formality | Fields used for branching, routing or a verdict contain **no prose** — enum, number, ID or boolean only |
| ✅ Regeneration | Delete `index/` and `map/` entirely, rebuild, **byte-identical**. Achieved literally rather than weakened: rows are sorted by uid before insert and **no timestamp is written**, since the commit SHA already identifies what the index was built from |
| The empty-query state | A query against an empty `kb/` returns **`searched_empty` explicitly**, never a bare 0 |
| Coordinates mandatory | No code path can return a hit without `repo@sha:path#locator` |
| Non-zero per source | Each adapter asserts a non-zero document count for its source; a source dropping to zero **fails the build** (§1) |

### B · Retrieval (F1 · F6 · F7 · F8)

| Check | Pass condition |
|---|---|
| ✅ Korean queries | 2, 3 and 4-character queries and partial words all hit (§3) |
| ✅ Profile divergence | The same question returns a **different top three** under lens 5 and lens 4 — verified **disjoint** on the real corpus: lens 5 lands in `kb/literature/`, lens 4 in `kb/expertise/`. Identical would mean the profile is decorative |
| Tier cross-check | An `evidence: assumed` file planted under `evidence/measured/` **is caught** |
| Decay detection | F7's two defects (missing generator, 40 vs 42) are **rediscovered automatically** |
| Tier carried | Every hit carries `evidence` and `tier`. A hit lacking them cannot be returned |

### C · Round trip (F4 · F5 · F9)

| Check | Pass condition |
|---|---|
| `kb_gaps` | For `bleach_photons` × G10, returns exactly *"BLOCKED, no supplying candidate"*. **v1's primary product** |
| Defect report | The `has_falsifier = 0` list is produced |
| Challenge routing | A raise without `falsifier_cited` is **refused**; with it, routes by type across all four paths |
| The literature route | For `resolvable_by: literature`, decides only whether the locator exists, and returns `unknown` otherwise |
| Oracle regression | F9 — breaking a profile makes a test **fail** |

### D · Refresh and isolation — **weekly automation is deferred**

> **Decision: the weekly consolidation is built later.** So two weeks of unattended
> operation drops out of the acceptance criteria.
>
> **The refresh itself cannot be deferred.** BD `I-076` names a stale index as one
> of the two ways a KB dies, and [PLAN.md](PLAN.md) §1.2 shows the early symptom
> already present. Deferring the scheduler **moves the refresh to a human**, and
> the defence has to move with it.

| Check | Pass condition |
|---|---|
| Explicit re-index | `librarian reindex` rebuilds in full from one command. Never incremental |
| **Self-reported decay** | When `manifest.json`'s SHA ≠ the current repo SHA, **every response carries `index_stale: true`** |
| Strict mode | Under `--strict` a stale index **refuses** to answer (the default is failure — constraint ①) |
| Proposal isolation | No path lets LLM output leave `store/inbox/` |
| `publish-gate` | A write of unpublished content to a public path is blocked, **proved by a test**. Includes `kb/08-retrieval/sessions/` → [PLAN.md](PLAN.md) §6.1 |

**The `index_stale` flag is the substitute for the scheduler.** Cron keeps the
refresh from being forgotten; the flag keeps a forgotten refresh from being
hidden. One of the two must exist, and the flag costs less while making the
failure loud.

The `export/` reachability check moves to MIGRATION Step 3 — the wiring itself is
Step 3, so it cannot be a Step 0 criterion.

### E · Condition for starting migration

**A · B · C · D all pass, plus the broken-reference CI check is live**
([MIGRATION.md](MIGRATION.md) Step 2).

That last item is not in A–D because it goes into **BD and MS**, not Librarian.
Librarian passing on its own, with no defence in the two repos, lets §1's silent
failure happen during the migration itself.

---

## 5. The order

```
Step 0  build + fixture verification        ← this document
          A structure → B retrieval → C round trip → D refresh → E ready
          (weekly automation sits outside Step 0)
Step 1  absorb (both sides alive)            MIGRATION.md
Step 2  update references (the real work)
Step 3  wire export/
Step 4  prove equivalence
Step 5  delete
```

**No source repository changes by one character during Step 0.** Fixtures are
copies and the `export/` wiring is Step 3, so the whole of Step 0 is reversible —
deleting this repository undoes it.

---

## 6. Decisions

| # | Decision | Value | Grounds |
|---|---|---|---|
| 1 | Tokenizer | **`trigram` + 2-char `LIKE` fallback** | §3, measured. Fixed at table creation |
| 2 | Morphological analyzer | **not used** | Reproducibility over ranking quality (BD `I-052`) |
| 3 | Are nine fixtures enough | one claim = one fixture, held as a rule | A new claim in the design means a new fixture |
| 4 | Unattended operation window | **deferred** with the weekly job | `index_stale` self-reporting is required instead (§4-D) |
| 5 | Fixture disposal | when MIGRATION Step 1 begins | Otherwise the same entry exists twice |
