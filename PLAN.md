# Librarian — build plan

Drafted 2026-09-06 · status `draft`
Grounded in the three live remotes, read 2026-09-06 (§1)

A knowledge agent that the other three talk to over MCP:
[agentic-microscope](https://github.com/kyu-softmatter/agentic-microscope) (experiment) ·
[Brownian-Dynamics-Agent](https://github.com/kyu-softmatter/Brownian-Dynamics-Agent) (simulation) ·
[research-topic](https://github.com/kyu-softmatter/research-topic) (proposal and validation).

> **Note on quotations.** BD's contracts (`knowledge/wiki/CLAUDE.md`, its paper
> distillations, its `entries/` claims) are written in Korean. Quotations from
> them below are translated; the locator is given so the original can be read.

---

## 0. Scope

Decided 2026-09-06.

| | |
|---|---|
| **Identity** | **The fourth axis.** Custody, retrieval and interaction for knowledge. Not `research-topic`'s J1 — that repo stays with **proposal and validation** |
| **v1** | **Librarian for the microscope agent only.** Then simulation (BD), then research (RT) |
| **Data** | Structure first, verified second, migrated third → [BUILD.md](BUILD.md) · [MIGRATION.md](MIGRATION.md) |
| **Visibility** | **public** — so `publish-gate` (§6.1) moves to Phase 0 |
| **Weekly consolidation** | **Deferred.** Replaced for now by `index_stale` self-reporting → [BUILD.md](BUILD.md) §4-D |

### 0.1 What v1 contains

| | v1 (MS) | v2 (BD) | v3 (RT) |
|---|---|---|---|
| Adapters | `kb/` 5 kinds · `data/*.yaml` · `docs/` | `wiki` · `source` · `entries` · `runs` | `design/` |
| Profiles | **lens 5 + lens 4** | `bd:s1`–`s8` · `lit-*` | `V1` · `V2` |
| Subject folders filled | `00` `01` `02` `03` `07` `08` | `05` `06` | — |
| Acquisition index (`envelope.sqlite`) | **excluded** → §0.3 | ★ first | — |
| Crosswalk (row 2) | **impossible — the BD side does not exist yet** | ★ first | — |
| `challenge/` routing | within MS only | across repos | the literature route |

> **All eight `kb/` folders are created in v1. Only their contents stay empty.**
> rt `kb-schema.md` §0: *"Filling before the form is fixed means throwing away
> what was filled when the form changes."* Without the folder, v2 would have to
> decide the shape a second time.

### 0.2 What v1 delivers

Read off the MS repository. **Both work with repository files alone and wait for
nothing.**

**① `kb_gaps` — which gate is `BLOCKED`, and for want of which input.**

`docs/07` Phase 0 records `power_at_sample_mw` as *"the largest effect, still the
top blocker"*, and states that until it lands *"every dose/SNR number stays
relative, and gates that need it keep returning `BLOCKED` by design."*
`bleach_photons` is empty for every dye in `data/fluorophores.yaml`, so G10 has
nothing to count against.

**This is the one v1 product that `grep` cannot produce.** It needs three places
crossed: empty fields in `data/*.yaml` × the field each gate requires × the
blocker list in `docs/07`. Joining those three is the adapter's job.

**Built 2026-09-06** (`python -m librarian.cli gaps --repo ms`). It derives both
blockers from the files, reading neither of the prose statements above:

| registry | field | gate | filled / total |
|---|---|---|---|
| `data/fluorophores.yaml` | `bleach_photons` | **G10** | **0 / 17** |
| `data/light_sources.yaml` | `power_at_sample_mw` | — | **0 / 6** |
| `data/fluorophores.yaml` | `lifetime_ns` | G20 | 11 / 17 |
| `data/particles.yaml` | `source` | — | 4 / 8 |

**② `kb/literature/` — the first entry.** Currently **0 entries**, with a README
and `_template.md` waiting. MS's own words: *"what sits in this folder is exactly
what is worth measuring next."* It is the only KB folder v1 can fill.

### 0.3 What v1 defers, and what that costs

| Deferred | Why |
|---|---|
| `envelope.sqlite` — the quantitative index of 2,343 acquisitions | The records live in `D:\data`, outside the repository. Access is a v2 decision |
| Indexing the analysis code (`D:\codes`) | Same access problem |
| BD · RT adapters | Adapters are **additive** — bolting one on later does not reshape anything |
| Row 2 crosswalk | Nothing to map until BD's 42 distillations arrive |
| Weekly automation | Replaced by `index_stale` (§6) |
| `05` · `06` contents | BD's domain |

**Excluding `envelope.sqlite` changes what v1 is.** Repository files alone give
roughly 100–150 documents, and at that size FTS5 is honestly overkill — `grep`
would nearly do. So v1's value is not search volume. It is **the structure, the
gap analysis, and the first retrieval feedback.**

**Half of the original motive moves to v2.** *Preparing for data to accumulate*
is, in v1, preparing the **form**; indexing the acquisitions themselves comes
later. That is the order rt `kb-schema.md` §0 asked for on independent grounds.

> **One thing is not deferred: the tokenizer.** v1 is MS-only and MS prose is
> English, so `unicode61` would do. But when BD (Korean prose) arrives in v2,
> `unicode61` returns **0 hits, not an error** ([BUILD.md](BUILD.md) §3, measured).
> So v1 ships `trigram` + a two-character `LIKE` fallback. The reason is not
> re-index cost — it is that the failure would be silent.

---

## 1. Verified facts — what this plan rests on

Read off the three remotes on 2026-09-06. What was checked and what was not are
kept apart.

### 1.1 Corpus size — FTS5 is justified once BD lands

| Store | Measured |
|---|---|
| BD `knowledge/entries/*.json` | **135** |
| BD `knowledge/source/papers/*.md` | **42** (+ `INDEX.md`) |
| BD `knowledge/source/books/` | **2** |
| BD `knowledge/wiki/**/*.md` | **44** (benchmarks 5 · concepts 3 · findings 23 · questions 2 · systems 11 · techniques 2) |
| BD `runs/*/record.json` | **256** |
| MS `kb/` | **40** (calibrations 4 · decisions 20 · expertise 6 · literature **2 = README + template only** · systems 8) |
| **Total** | **~520 documents** |

BD `tools/kb.py` notes: *"A SQLite + FTS5 store is the plan, but it is overkill
below 100 runs."* **There are 256 runs.** That threshold has passed — but it
passes in **v2**, not v1 (§0.3).

### 1.2 Index decay has already started — I-076, observed

`knowledge/source/papers/INDEX.md`, line 1 (translated):

```
<!-- Generated: docs/tools/wiki_index.py — do not edit by hand -->
```

- **`docs/tools/` does not exist in the repository.** The generator is gone and
  the generated file remains.
- `INDEX.md` states the entry count as **40**. There are **42** files.

So a file that says *do not edit by hand* is being read by both repos, with no
surviving means of regenerating it, already two entries behind. This is the early
form of what BD `I-076` predicted — *all the files are there and search finds
nothing* — and it is **the most checkable single reason for this project.**

### 1.3 BD carries an unresolved schema split inside itself

BD `docs/03-knowledge-base.md` §1 calls it *"the largest piece of debt in the
repository"*:

| | `wiki/` + `source/` | `entries/` |
|---|---|---|
| Form | Markdown + YAML frontmatter | flat JSON |
| Written by | a human or an agent, deliberately | `tools/kb.py add` |
| Read by | skill `bd-knowledge` | `tools/kb.py query` |
| Size | 44 + 44 | 135 |

*"A lesson filed in one is not found by a tool reading the other. … the honest
interim rule is **query both**."*

**Turning "query both" into one query is the first measurable win — in v2.**

### 1.4 Row 2 is the sharpest gap, and the mapping is 1→N

rt README §2.1 row 2: BD holds 42 literature distillations; MS holds an **empty
folder built to receive exactly that** (`kb/literature/` — README and
`_template.md` only).

The two sides store at different granularity. MS `kb/literature/README.md`:

> *"One file per quantity per subject. `bleach-photons-alexafluor488.md`, not
> `smith-2019.md`: the unit of storage is the number a gate consumes, not the
> paper it came out of. One paper supplying three quantities becomes three files."*

BD's unit is one paper per file, with a `provides:` array.

**So the crosswalk is 1→N, and BD's `provides` array is already the decomposition
key.** `mason-weitz-1995` carries `provides: [gser-formula, msd-to-moduli,
newtonian-limit-check]` — three MS-shaped files. This is not a schema to
negotiate; it is a field that already exists on both sides.

### 1.5 The fourth convergence — enforceable at the transport layer

All three repos independently reached the same rule: **a published number is
unusable without the conditions under which it holds, and it never counts as a
measurement.**

| Repo | How it says it |
|---|---|
| research-topic | `literature.conditions` |
| MS | `evidence: assumed`, never `measured`, so `advances: NO`. `## Transfer conditions` is mandatory |
| BD | provenance `from_paper` · `assumed` · `derived` plus a **tier**; a derived value is recomputed, never trusted as written |

BD recorded the cost of getting this wrong: `T = 300 K` filed as tier 1
(measured) when it was a choice, propagating **−4 % to −14 % into every `τ_B`
downstream.**

**→ Design consequence: every hit carries `evidence` / `tier` / `provenance`.**
A hit without a tier is not returned. Mis-tiering then shows up at transport time.

### 1.6 The two repos run on different machines

MS `.mcp.json`:

```json
"command": "C:\\Users\\<lab PC>\\venvs\\auto_microscope\\Scripts\\python.exe"
```

MS's MCP server holds hardware on the **lab Windows PC**. BD runs on macOS under
conda `simulation_bot`. **A shared local filesystem cannot be assumed.**

All four repositories are public, so `git fetch` is a platform-independent
ingest channel — and the commit SHA becomes the index's provenance.

### 1.7 Nothing in either repo reads its KB at runtime

Checked by grep over code, tests and agent definitions.

| Question | Answer |
|---|---|
| Do MS gates read `kb/` at runtime? | **No.** They read `data/*.yaml` (`optics/components.py` → `fluorophores.yaml` · `filters.yaml` · `pixel_size.yaml`) |
| Do MS tests read `kb/` files? | **No.** Comment citations only |
| Does the BD pipeline read `knowledge/`? | **No.** Only `tools/kb.py`, a CLI tool |
| Does BD `pytest` read `wiki/benchmarks/`? | **No.** The `benchmark` marker is used in 10+ places, all inside `test_s*.py`, with values **hardcoded** |
| `tests/test_knowledge.py` | **Does not exist**, though `conftest.py` registers the marker for it |

**The real consumers are LLM agents and humans, not code** — and the MS lenses
read with `tools: Read, Grep, Glob`, with **no MCP tool declared.**
→ [MIGRATION.md](MIGRATION.md) §1 · §3

### 1.8 What the first scan found — 2026-09-06

Running the four MS adapters and the drift report over `agentic-microscope`
@ `196cdf1` produced **544 documents from 59 files**, with every candidate file
accounted for, and four findings.

| Finding | Detail |
|---|---|
| **`G2` · `G3` · `G4` are declared and not implemented** | `docs/04-decision-engine.md` gives each a threshold and `BLOCKED` as its default (`G2` emission collection `>= 15%`, `G3` excitation blocking `>= 5 OD`, `G4` crosstalk `< 5%`) and `docs/05` repeats them. **None appears in any Python file.** They are the optics spectral gates, and `optics/checks.py` states its checks as questions — *"Does this line actually excite this dye through this path?"* — carrying no gate id, so nothing ties the implementation to the declaration |
| **The exemplar challenge entry cannot be challenged** | `kb/expertise/oil-objective-trapping-in-water.md` is the entry rt README §2.2 holds up as *"a challenge that was upheld."* It has `evidence: measured`, `review_after`, `supersedes: null` — and **no falsification section**, where five of the six entries beside it have one. By `kb-schema.md` §4.7 an entry with no falsifier cannot be challenged, so the model case is exempt from the rule it models |
| **`bleach_photons` is absent for all 17 dyes** | G10 has nothing to count against, as `photo/gate.py` says. Derived, not read |
| **`power_at_sample_mw` is empty for all 6 sources** | The key exists on almost every line and its value is `{}`. `docs/07` Phase 0 calls it the top blocker |

**Three of the four are about the gap between a declaration and its
implementation**, which is what `kb-schema.md` §6 left open as *"detecting when
`rigor/` drifts from BD's and MS's real files."* None of them was found by
reading a sentence that says so.

> **The report is only useful if it is short.** Four false-positive classes were
> removed while building it, and each cost more than it looked like:
>
> | Removed | What it did |
> |---|---|
> | Key existence read as presence | Reported `power_at_sample_mw` as supplied by 5 of 6 sources — the opposite of the truth |
> | Bare identifiers read as field reads | Attributed `data/particles.yaml > product` to G11 because that gate's function has a local called `product` |
> | Two examples read as a folder convention | Reported 18 of 20 decision logs as missing a falsifier, burying the one entry that matters |
> | A prose mention read as a declaration | Reported six of **MS's** gates as missing from BD, because BD's roadmap discusses the handoff in prose |
>
> The last two are the same failure in different clothes: **a linter that reports
> everything reports nothing.** Each is now a regression test.

---

## 2. Inherited constraints

rt README §0: the only things not to change are the six philosophy items and the
boundary table in `charter.md` §3 — both were inherited from the two working
repos or derived from where they independently converged, so they are not one
repo's to change alone. Librarian is bound the same way.

| # | Constraint | What it forbids here |
|---|---|---|
| ① | The default is failure, not passing | No results is `searched_empty`, and an unrecorded query is `not_searched` — never "fine" |
| ② | The LLM does not originate numbers | The refinement step emits citations and locators only. No value summaries |
| ③ | Every judgment carries the check that would overturn it | Every hit carries its falsifier |
| ④ | Natural language is not state | Any field used for branching, routing or a verdict is an enum, a number, an ID or a boolean |
| ⑤ | In rigor disagreement is a bug; in value it is the product | Librarian does not handle value → no aggregation, no averaging |
| ⑥ | The canonical source of value is not a textbook | Out of scope (J2) |

From `charter.md` §5: **does not set values or thresholds** · **does not run
simulations or experiments** · **does not settle a challenge whose falsifier it
cannot run** — it routes.

### 2.1 A conflict that only looks like one — the relevance score

`kb-schema.md` §3 forbids `value_score: 0.7`, because a score makes averaging
possible and averaging destroys divergence.

**A search relevance score is not caught by this** — a rank orders retrieval, it
does not assert worth. But the danger reappears at exactly that point:

> **Rank is returned, never stored in an entry.** Stored, it becomes a scalar
> claim that "this one matters more," and §3's prohibition returns in new dress.

---

## 3. Architecture

**Librarian owns the canonical store.** This is the consequence of being the
fourth axis rather than rt's J1: the KBs of the three agents move here and are
then deleted from them ([MIGRATION.md](MIGRATION.md)).

Two things keep that from being irreversible in the way `charter.md` §4 warns
about (*"indexing is reversible; migration is not"*):

1. **Deletion is the last step, gated on an equivalence proof** (MIGRATION §4).
2. **A generated read-only copy goes back to each repo** (`export/`), so the
   consumers that read with `Grep` keep working offline (§1.7).

```text
        ┌─────────────────── Librarian (public) ────────────────────┐
        │                                                           │
        │  cache/       shallow clone × 3, read-only     ◆ derived  │
        │       │                                                   │
        │       ▼  adapters/   parse each repo's frontmatter        │
        │                                                           │
        │  kb/          ★ CANONICAL — the store itself              │
        │    00-decisions 01-materials 02-hardware 03-control       │
        │    05-physics 06-simulation 07-sources 08-retrieval       │
        │       │                                                   │
        │       ├──▶ index/kb.sqlite      ◆ FTS5 (trigram) + metadata         │
        │       ├──▶ map/                 ◆ 04-agents · manifest    │
        │       └──▶ export/{ms,bd}/      ◆ read-only, sent back    │
        │                                                           │
        │  store/       ● published: challenge · digest · inbox     │
        │  profiles/    caller_profile YAML                         │
        │  mcp/         the server                                  │
        └───────────────────────────────────────────────────────────┘
                 │ read-only                    │ generated copy
                 ▼                              ▼
        BD · MS · research-topic        MS/kb-export · BD/knowledge-export
```

### 3.1 Three invariants

Break any one and Librarian becomes an enforcer, violating `charter.md` §5.

1. **Never write into the source repositories.** Writes go to `kb/`, `store/`
   and `export/`; anything landing in BD or MS arrives as a pull request.
2. **Entry files are canonical; the index is derived.** No code path edits an
   index by hand (`kb-schema.md` §5). Deleting `index/` and `map/` must lose
   nothing.
3. **Every hit carries `repo@sha:path#locator`.** A hit without coordinates is
   not returned. This is BD's handbook contract — *a claim can be walked back to
   the page it came from without the book being in the repository* — extended to
   the whole index.

### 3.2 Why vector search is not the primary path

BD `I-052`: a question's fate is decided by whether a search returns anything,
not by an LLM vote. Embedding similarity is reproducible but **cannot say in
coordinates why a hit matched.**

**MS reached the same conclusion independently.** `docs/02` §1: *"Only markdown +
SQLite. Why no vector DB: embedding search cannot explain 'why was this precedent
selected,' and it cannot trace back the cause of a bad recommendation."*

→ **FTS5/BM25 is the primary path.** Embeddings, if ever added, are a reranking
layer only, and never participate in deciding whether a result exists.

---

## 4. Index design

### 4.1 Document normalization

Adapters flatten several formats into one row, keeping **branchable fields
physically separate from prose** (constraint ④).

```sql
doc(
  -- coordinates (IDs and enums, never free text)
  uid            TEXT PRIMARY KEY,   -- <repo>:<path>#<locator>
  repo           TEXT,               -- enum: librarian | ms | bd | rt
  commit_sha     TEXT,
  path           TEXT,
  locator        TEXT,               -- section · table row · JSON pointer

  -- branchable (enum / number / bool)
  kind           TEXT,   -- paper|book|entry|run|wiki_*|expertise|literature
                         -- |calibration|decision|system|challenge|retrieval
  origin         TEXT,
  evidence       TEXT,   -- measured | assumed | confirmed_default | null
  tier           INTEGER,
  provenance     TEXT,   -- from_drawing|from_paper|from_knowledge|assumed|derived
  reproduced     TEXT,   -- yes | no | partial | null
  lab_authored   INTEGER,
  advances       INTEGER,  -- 1 only where evidence = measured
  review_after   DATE,
  superseded_by  TEXT,
  has_falsifier  INTEGER,  -- decides whether it can be challenged
  doi            TEXT,

  -- prose (no code branches on these)
  title          TEXT,
  body           TEXT,     -- FTS5 target
  conditions     TEXT      -- conditions of validity, as published
)
```

`has_falsifier` matters more than it looks. `kb-schema.md` §4.7: *"An entry with
no falsifier cannot be challenged. That is a defect in the entry — philosophy ③
says every judgment carries the check that would overturn it — and not a gap
here."* **So the list of `has_falsifier = 0` entries is itself a defect report.**

### 4.2 Field mapping — from each repo's declared contract

Not invented; read from what each repo already declares for machines.

| Source | Contract | Fields it supplies |
|---|---|---|
| BD wiki/source | `knowledge/wiki/CLAUDE.md` frontmatter (`source_frontmatter_required` · `precedence` · `wiki_types`) | kind · origin · lab_authored · reproduced · cites |
| BD entries | `tools/kb.py` `SCHEMA_ENTRY` · `ORIGINS` | kind · origin · system_tags · source |
| BD runs | `bdbot.record/0.1` | tier · dimensionless · observables · provenance |
| MS literature | `kb/literature/_template.md` | evidence · confidence · gate · scope · measured_on · review_after · superseded_by_measurement |
| MS expertise | live entry frontmatter (rt `Q-002` found the form domain-neutral) | question · evidence · scope · applies_to_systems · review_after · supersedes |
| MS registries | `data/*.yaml` | the field a gate consumes, and whether it is empty |
| rt | `kb-schema.md` §4.1–4.7 | the seven entry kinds |

> **BD `wiki/CLAUDE.md` states it directly (translated): "code parses the
> frontmatter rather than hard-coding paths."** Adapters follow that instruction.
> Hard-code a path and Librarian reproduces §1.2's failure the next time a folder
> moves.

### 4.3 Drift detection — the index catches its own decay

An answer to `kb-schema.md` §6's open item: *"Detecting when `rigor/` drifts from
BD's and MS's real files. Hand-maintained `implemented_in` goes stale."*

Deterministic report on every build:

| Check | What it catches |
|---|---|
| `review_after < today` | Expired entries |
| `superseded_by_measurement` target missing | A broken supersession chain |
| `has_falsifier = 0` | Entries that cannot be challenged — an entry defect |
| Generated file with no generator | §1.2 — orphaned artefacts |
| Declared count ≠ actual file count | §1.2 — an index left behind |
| `[[wikilink]]` / relative path with no target | Broken cross-references |
| `reproduced: no` cited as grounds | Violates BD's wiki discipline |
| `evidence: assumed` with `advances: YES` | **§1.5's −4 % to −14 % incident, recurring** |
| Path tier ≠ frontmatter `evidence` | Folder and field disagree → [TREE.md](TREE.md) §4 |

**The last three are the value here.** The rest is hygiene; these three detect
the recurrence of accidents both repos paid for and wrote down.

---

## 5. The MCP tool surface

### 5.1 Context-aware retrieval is a profile, not a judgment

The answer to *"a question that carries the calling agent's context"* is already
in BD `I-053` (translated):

> *Perspective separation is not produced by separate stores but by **a different
> search query per persona.** Consequence: a large corpus costs nothing in
> context — it is an index, not context.*

→ **`caller_profile` is a versioned config file, not a query the LLM composes each
time.**

```yaml
# profiles/ms-lens5-photo-perturbation.yaml
id: ms:lens-5-photo-perturbation
kind_weight:                    # a weight, never a filter
  calibration:     2.0          #   measured here; outranks anything published
  literature_form: 1.8
  registry:        1.6
  agent:           0.5
boost:
  gate:  [G10, G20, G21, G22]           # read off photo/checks.py docstrings
  field: [bleach_photons, lifetime_ns, power_at_sample_mw, ...]
  path_prefix: [data/fluorophores.yaml, kb/literature, ...]
demote:
  reproduced: {"no": 0.7}               # demoted, never excluded
return_always: [evidence, tier, has_falsifier, conditions, review_after]
```

> **Two filters in the first draft of this section each removed the answer.**
> Building it showed both:
>
> | Drafted as | What it did | Now |
> |---|---|---|
> | `require_fields: [evidence, tier]` — *"a hit without these is dropped"* | **495 of 544 MS documents carry no evidence tier**, including every `docs/` section. Asked what G10 checks, the profile would drop the answer | `return_always` — the tier is **carried**, which is what stops a caller mistaking `assumed` for `measured`. A hard filter is opt-in per query (`require`), not per profile |
> | `exclude: reproduced: [no]` | Most registry entries state `verified: false` on purpose — the headers say the values are catalog nominals whose wings are wrong. `data/fluorophores.yaml > AlexaFluor488` is exactly what this lens needs | `demote` — BD's rule is not to raise an unreproduced value as **grounds**; it is still the right pointer |
>
> **Both mistakes have the same shape as the linter mistakes in §1.8: a filter
> that looks like rigour and removes the thing being looked for.**

**v1 profiles: `ms:lens-5-photo-perturbation` and `ms:lens-4-sample-optics`.**
A pair, not one — the acceptance criterion is that the same question returns
**different top results** under each ([BUILD.md](BUILD.md) §4-B), and one profile
cannot demonstrate that. These two consume different corpora: lens 5 owns
`bleach_photons` and G10, lens 4 owns G15–G19 and the `kb/expertise/` entries on
immersion media, coverslip thickness and medium refractive index.

Later: `ms:lens-{3,6,8}` (v1, if useful) · `bd:s1`–`s8` · `bd:lit-*` (v2) ·
`rt:V1` · `rt:V2` (v3).

### 5.2 Eight tools

Six read, two write. **Writes touch `kb/` and `store/` only.**

| Tool | Signature | Returns |
|---|---|---|
| `kb_search` | `(question, caller_profile, limit?, require?)` | hits with `repo@sha:path#locator`, `evidence`/`tier`/`advances`, `has_falsifier`, and `index_stale`. Zero results is **`searched_empty`, distinct from `not_searched`** (constraint ①). Terms of 3+ characters go to FTS5 `MATCH` (bm25-ranked, OR-combined); shorter ones to `GLOB` → [BUILD.md](BUILD.md) §3 |
| `kb_get` | `(uid)` | body plus full frontmatter |
| `kb_neighbors` | `(uid, relation)` | `cites` / `used_by` / `supersedes` graph |
| `kb_supplies` | `(field \| gate)` | what supplies that registry field or gate. **`bleach_photons` × G10 is the live case** |
| `kb_gaps` | `(caller_profile)` | gates `BLOCKED` for want of an input · registry fields still empty · `has_falsifier = 0` entries. **v1's primary product** (§0.2①) |
| `kb_stale` | `()` | the §4.3 drift report |
| `kb_challenge_raise` | `(target_uid, doubt_kind, falsifier_cited, …)` | writes `store/challenge/` and **routes by falsifier type**. Refused without `falsifier_cited` |
| `kb_feedback` | `(query, caller_profile, returned, cited, verdict, …)` | writes `kb/08-retrieval/sessions/` → [FEEDBACK.md](FEEDBACK.md) |

**Two things `kb_challenge_raise` enforces** (`kb-schema.md` §4.7):

- `falsifier_cited` is **mandatory** and must point **into the target**, not into
  the challenger. That is what makes a challenge a work order rather than an
  argument.
- Routing is decided by **the falsifier's type, not the sender**: a measurement →
  MS · a run → BD · a condition of validity → RT · none available → a human.
- `depth` increments and `cost` is recorded. Without the bound the loop
  circulates doubt instead of topics (`C-001`).

**The only thing Librarian may settle:** for `resolvable_by: literature`, the
**presence or absence of a locator** — does the cited section exist, does it state
the condition. Everything else returns `unknown`. `kb-schema.md` §6 records this
as *"the largest unclosed item in this document"* (`C-007`); **Librarian does not
close it, and answers a weaker question deterministically instead.**

---

## 6. Weekly consolidation — ⏸ deferred (2026-09-06)

> **Deferred by decision.** The design below stands but is out of v1's acceptance
> criteria. Index refresh is handled by `librarian reindex` plus `index_stale`
> self-reporting → [BUILD.md](BUILD.md) §4-D.
>
> **The refresh itself cannot be deferred.** BD `I-076` names a stale index as one
> of the two ways a KB dies, and §1.2 shows the early symptom already present.
> Deferring the scheduler moves the refresh to a human; the flag is what keeps
> that from being silent.

When it is built, it splits in two — constraint ② requires it.

### Tier 1 — deterministic, always runs

**`0 18 * * 6`** (Sat 18:00 UTC = **Sun 03:00 KST**), on GitHub Actions so it does
not depend on a laptop being awake or on an API budget.

1. `git fetch` × 3, record the new SHAs
2. Rebuild the index in full — never incrementally; the rebuild *is* canonical
3. Diff against last week's `manifest.json` → the weekly delta
4. Run the whole §4.3 drift report
5. Commit `store/digest/<ISO week>/`
6. Open an issue **on this repository** if drift has new entries — never on BD or MS

### Tier 2 — LLM refinement, proposals only

Everything lands in `store/inbox/` and reaches nothing without human approval.

| Task | Output | Why a proposal |
|---|---|---|
| New BD paper → MS `_template.md` shape (1→N, §1.4) | `inbox/crosswalk/` | The value is MS's to own (`charter.md` §3) |
| Repeated patterns across runs → `entries/` candidates | `inbox/entries/` | BD owns `entries/` |
| Expired `review_after` → challenge drafts | `inbox/challenge/` | Whether `falsifier_cited` is apt is a human call |
| `kb_gaps` rollup → "what to measure next" | `digest/worklist.md` | MS: *"what sits in this folder is exactly what is worth measuring next"* |

**Forbidden in Tier 2:** originating or summarizing numbers (②) · aggregating
across entries (⑤) · assigning `evidence: measured` · editing a source repo (§3.1).

### 6.1 The publish gate — required, and sooner than expected

rt README §8 left `T-019`① open:

> *"The topic assessments that will accumulate in the KB are unpublished research
> directions. … it stops being a question about who can read the repo and becomes
> **a rule about what J1 is allowed to write into it.** That rule does not exist
> yet, and it has to before the first topic assessment lands: in a public repo,
> deleting the file afterwards does not undo the disclosure."*

This repository is public, so the rule belongs in Phase 0. **The path that opens
first is not the digest** — the digest is deferred — **it is
`kb/08-retrieval/sessions/*.json`, which stores query text.**
*"bleach photons for AlexaFluor488 at 470 nm"* is harmless, but **what someone was
looking for is what they are about to do.** Three options, to be settled when
`08-retrieval` is implemented: hash the query only (oracles then cannot be
re-run) · gitignore `sessions/` and commit `oracles/` only · commit as-is.
**Until then session files are not committed** (the default is failure).

Two rules inherited regardless:

- **Folder-level disclosure boundaries.** BD solved this already —
  `source/papers/` in-git, `source/lab/` gitignored — because *"what has to be
  protected is not the author but the fact that it is not yet published."*
  `kb/07-sources/raw/` inherits it.
- **No attributions.** rt `T-018` · `T-035`: *citations stay, attributions go.*
  No output of this repo says "X would find this uninteresting."

---

## 7. Phases

Each phase carries an exit condition. A phase without one does not end.

### Phase 0 — skeleton and adapters (read-only)

| Task | Exit condition |
|---|---|
| Repository, `kb/` 8 folders, uniform 5-slot shape | All eight exist with the same shape; branchable fields hold **no prose** |
| `cache/` fetch × 3 | `manifest.json` records three SHAs |
| MS adapters (`kb/` · `data/*.yaml` · `docs/`) | Every MS document lands in one `doc` table with **zero rows lacking coordinates** |
| §4.3 drift report | **Rediscovers §1.2's two defects automatically** (missing generator, 40 vs 42) |

> The last exit condition is the point of Phase 0. A tool that cannot find the
> defects a human already found by hand is not yet doing anything.

### Phase 1 — retrieval and MCP

| Task | Exit condition |
|---|---|
| ✅ FTS5 (`trigram` + `GLOB` fallback), `kb_search` | Korean and English queries of 2, 3 and 4 characters all hit ([BUILD.md](BUILD.md) §3) |
| ✅ `profiles/` — lens 5 and lens 4 | The same question returns **different top three** under each — verified disjoint: lens 5 lands in `kb/literature/`, lens 4 in `kb/expertise/` |
| ✅ **`kb_gaps`** | For `bleach_photons` × G10, returns 0 of 17 with nothing supplying it (§0.2①) |
| `kb_get` · `kb_neighbors` | pending |
| MCP server registered | The tools are callable from a Claude Code session in the MS repo |

### Phase 2 — interlocks (**before** any KB content)

| Task | Exit condition |
|---|---|
| `librarian reindex` + `index_stale` | A stale index cannot answer silently; `--strict` refuses |
| Regeneration | Delete `index/` and `map/` entirely, rebuild, **byte-identical** |
| ID issuance | `kb-schema.md` §6's *"who issues entry IDs — sequential numbers collide under parallel writes"* → **content-hash**, inheriting BD's `run_id` approach |
| `publish-gate` (§6.1) | A write of unpublished content to a public path is blocked, **proved by a test** |

### Phase 3 — the first entry, and feedback

| Task | Exit condition |
|---|---|
| `kb/literature/` first entry | Every mandatory section of MS `_template.md` filled; merged into MS as a **pull request** |
| `kb/08-retrieval/` | An oracle catches a regression: break a profile on purpose and **the test must fail** ([FEEDBACK.md](FEEDBACK.md) §5) |

### Phase 4 — migration

→ [BUILD.md](BUILD.md) for the acceptance gate, [MIGRATION.md](MIGRATION.md) for
the five steps. **Deletion is Step 5.**

### Not in scope

- **J2 (topic selection)** — doing it would violate `charter.md` §5's *"does not
  settle a topic's value."*
- **J3 (definitions of rigor)** — RT owns it; Librarian detects `implemented_in`
  drift only.
- **Monorepo (option B)** — rt README §7 puts the decision after its Phase 1, and
  it is not Librarian's to make.
- **Retrospective validation of value** — rt `C-003` records that there is no
  answer yet.

---

## 8. Failure modes, named in advance

BD `I-075` and `I-076` diagnosed the two ways a KB dies. Librarian **is** the
defence against those two, so if it dies that way there is no defence left.

| Failure | Symptom | Defence |
|---|---|---|
| **Nobody fills it** (`I-075`) | `store/inbox/` piles up awaiting approval | Tier 1 runs without a human; the digest reports its own backlog |
| **The index goes stale** (`I-076`) | §1.2, recurring | Full rebuild, never incremental; `index_stale` on every response |
| **Generator and artefact separate** | §1.2, observed | Every generated file heads with its generator path and SHA; drift catches a missing generator |
| **Prose becomes state** (`I-133`) | Another agent cites a digest summary as grounds | Digests carry coordinates; summary paragraphs get no citable ID |
| **Librarian becomes an enforcer** | It sets a value, or settles a challenge | §3.1's three invariants |
| **Unpublished direction goes public** | Query text or a digest in a public repo | §6.1 `publish-gate`; sessions uncommitted until decided |
| **Rank becomes worth** | A score stored in an entry | §2.1 — returned, never stored |
| **A silently empty read** | A moved path returns 0 rows instead of an error | Adapters assert a non-zero count per source; a source that drops to zero fails the build |

The last row is BD's own recorded accident: `tools/kb.py` pointed at a renamed
path and *"simply reported 'run-less knowledge 0' for 126 existing entries. A
silently empty read is the same failure mode as an unwired checker."*

---

## 9. Decisions

### Settled

| # | Decision | Value | Grounds |
|---|---|---|---|
| 1 | Visibility | **public** | Decided 2026-09-06. `publish-gate` moves to Phase 0 |
| 2 | v1 scope | **MS only**, then BD, then RT | Decided 2026-09-06 |
| 3 | First build step | **Folder skeleton** | §4-A acceptance applies to the skeleton alone, so it is verifiable |
| 4 | v1 profiles | **lens 5 + lens 4** | A pair is required to prove profiles change results |
| 5 | Document language | **English** | Two of the three repos are English; this one is public with several participants |
| 6 | Tokenizer | **`trigram` + 2-char `LIKE`** | Measured, [BUILD.md](BUILD.md) §3. Fixed at table creation |
| 7 | Morphological analyzer | **Not used** | Reproducibility outranks ranking quality (`I-052`) |
| 8 | Embeddings | **Not in v1** | MS rejected vector search for the same reason (§3.2) |
| 9 | Write access to source repos | **None.** Pull requests only | §3.1; direct writes make migration irreversible |
| 10 | Offline read path | **`export/` generated copies** | MS lenses declare `Read, Grep, Glob` and no MCP (§1.7) |
| 11 | Paths | **ASCII.** Prose in any language | BD's `entries/` filenames already broke on Korean slugs; NFC/NFD splits them across macOS and Windows |
| 12 | `05` / `06` boundary | **The engine-swap test** | Checkable, so two people give the same answer ([TREE.md](TREE.md) §2-B) |
| 13 | Category 3's name | **`03-control`** | "Software" names three different things ([TREE.md](TREE.md) §2-C) |
| 14 | Number 04 in `kb/` | **Left empty** | The gap marks the write-authority split |
| 15 | `runs/` (256) | **Not migrated**; indexed only | Run provenance is BD's (`charter.md` §3) |
| 16 | `tools/kb.py` | **Retired** | Its `ENTRY_DIR` returns 0 silently |
| 17 | Broken-reference CI check | **Required at MIGRATION Step 2** | The only defence against §8's last row |
| 18 | Weekly automation | **Deferred** → `index_stale` | Decided 2026-09-06 |
| 19 | `cited` collection | **Reported by the caller**, never inferred | Inferred, it stops being a fact |
| 20 | Missing feedback | **`not_searched`** | Constraint ① |
| 21 | Oracle promotion | Two distinct index SHAs **+ human approval** | Blocks the self-confirming loop ([FEEDBACK.md](FEEDBACK.md) §5) |
| 22 | Fixture disposal | **When MIGRATION Step 1 begins** | Otherwise the same entry exists twice |

### Open — decided when the work reaches them

| # | Decision | Blocks |
|---|---|---|
| a | **`publish-gate` scope for `sessions/`** — hash · gitignore · commit as-is | `kb/08-retrieval` (Phase 3). Sessions uncommitted meanwhile |
| b | `D:\data` access — run on the lab PC, or ingest a metadata export | `envelope.sqlite` (v2) |
| c | Indexing `D:\codes` (the analysis code lens 6 reads) | Same access question (v2) |
| d | `entries/` (135) decomposition by `origin` | v2 |
| e | `export/` wiring — git subtree or generated commit | MIGRATION Step 3 |
| f | Tier 1 execution site | When the weekly job is built |
| g | Deletion timing | MIGRATION Step 4's proof |

---

## 10. References

| Document | Used for |
|---|---|
| rt `README.md` §1 · §2.1 · §2.2 · §4 · §7 · §8 | The three jobs · row 2 · challenge · phase form · option A · disclosure |
| rt `design/charter.md` §3 · §4 · §5 | Ownership boundaries · indexing ≠ migration · structural prohibitions |
| rt `design/kb-schema.md` §1 · §3 · §4.1 · §4.7 · §5 · §6 | Prose is not state · no scalar · literature schema · challenge · the index · open items |
| BD `docs/03-knowledge-base.md` §1 · §4 | The two-schema debt · provenance and tiers |
| BD `knowledge/wiki/CLAUDE.md` | The frontmatter contract (parse it, do not hard-code paths) |
| BD `tools/kb.py` | `ORIGINS` · the FTS5 plan · the silently empty read |
| MS `docs/02-knowledge-base.md` §1 · §2 · §6 · §7 · §8 | Storage layout · 3-tier normalization · the acquisition index · the parser spec · sample recipes |
| MS `docs/07-roadmap.md` Phase 0 | The top blocker, and gates `BLOCKED` by design |
| MS `kb/literature/README.md` · `_template.md` | Unit of storage · the `advances` rule · transfer conditions |
| MS `kb/expertise/oil-objective-trapping-in-water.md` | A challenge that was already upheld |
