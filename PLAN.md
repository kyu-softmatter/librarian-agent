# Librarian — build plan

Drafted 2026-09-06 · status `draft`
Grounded in the three live remotes, read 2026-09-06 (§1)
§3.3–§3.6 — what the librarian is, how a caller reaches it, and who the callers
are — added 2026-09-09

A knowledge **server** — deliberately not a fourth agent (§3.3) — that the other
three talk to over MCP:
[agentic-microscope](https://github.com/kyu-softmatter/agentic-microscope) (experiment) ·
[Brownian-Dynamics-Agent](https://github.com/kyu-softmatter/Brownian-Dynamics-Agent) (simulation) ·
[research-topic](https://github.com/kyu-softmatter/research-topic) (topic selection).

> **Note on quotations.** BD's contracts (`knowledge/wiki/CLAUDE.md`, its paper
> distillations, its `entries/` claims) are written in Korean. Quotations from
> them below are translated; the locator is given so the original can be read.

---

## 0. Scope

Decided 2026-09-06; the three rows citing §3.3–§3.5, 2026-09-09.

| | |
|---|---|
| **Identity** | **The fourth axis.** Custody, retrieval and interaction for knowledge. Not `research-topic`'s J1 — that repo keeps **J2** (topic selection) and **J3** (the form of a pass condition) |
| **Kind of thing** | **A server over a store, not a fourth conversational agent** → §3.3 |
| **Callers** | the three agents' lenses and personas, **and people** — each under a named profile, everyone through their own MCP client → §3.5 |
| **Where it runs** | **The microscope PC — all four systems, one machine** (decision 35). stdio, one process per session, and it stays correct through BD → §3.4 |
| **v1** | **Librarian for the microscope agent only.** Then simulation (BD), then research (RT) |
| **Data** | Structure first, verified second, migrated third → [BUILD.md](BUILD.md) · [MIGRATION.md](MIGRATION.md) |
| **Visibility** | **public** — so `publish-gate` (§6.1) moves to Phase 0 |
| **Weekly consolidation** | **Deferred.** Replaced for now by `index_stale` self-reporting → [BUILD.md](BUILD.md) §4-D |

### 0.1 What v1 contains

| | v1 (MS) | v2 (BD) | v3 (RT) |
|---|---|---|---|
| Adapters | `kb/` 5 kinds · `data/*.yaml` · `docs/` | `wiki` · `source` · `entries` · `runs` | `design/` |
| Profiles | **lens 5 + lens 4** | `bd:s1`–`s8` · `lit-*` · `human:*` | `V1` · `V2` |
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

**Excluding `envelope.sqlite` changes what v1 is.** This section first estimated
**100–150 documents** from repository files alone and concluded that FTS5 was
honestly overkill at that size — `grep` would nearly do. **The first scan
measured several times that** (§1.8), because normalization splits one file into
sections and one registry into entries. So the size argument no longer holds; the
conclusion does, for a different reason. v1's value is not search volume. It is
**the structure, the gap analysis, and the first retrieval feedback.**

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
| BD `knowledge/wiki/**/*.md` | **44** files, including the contract (benchmarks 5 · concepts 3 · findings 23 · questions 2 · systems 11 · techniques 2). **Entries** are fewer: `_`-prefixed templates and indexes make findings 22 and systems 9, and `benchmarks.yaml` lists **7 running** benchmarks rather than 5 files |
| BD `runs/*/record.json` | **227**, in **256** run directories |
| MS `kb/` | **40** (calibrations 4 · decisions 20 · expertise 6 · literature **2 = README + template only** · systems 8) |
| **Total** | **490 files** — and one file is many documents: MS's 59 files yield 513 indexed rows, because a section is the citable unit |

BD `tools/kb.py` notes: *"A SQLite + FTS5 store is the plan, but it is overkill
below 100 runs."* **There are 227 post-mortems across 256 run directories.**
That threshold has passed — but it
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

### 1.4 Row 2 is the sharpest gap — and the decomposition key it named does not exist

rt README §2.1 row 2: BD holds 42 literature distillations; MS holds an **empty
folder built to receive exactly that** (`kb/literature/` — README and
`_template.md` only).

The two sides store at different granularity. MS `kb/literature/README.md`:

> *"One file per quantity per subject. `bleach-photons-alexafluor488.md`, not
> `smith-2019.md`: the unit of storage is the number a gate consumes, not the
> paper it came out of. One paper supplying three quantities becomes three files."*

BD's unit is one paper per file.

> **⚠ The rest of this section was wrong, and it was generalized from the one
> file it cites.** It read: *"BD's unit is one paper per file, with a `provides:`
> array. So the crosswalk is 1→N, and BD's `provides` array is already the
> decomposition key. `mason-weitz-1995` carries `provides: [gser-formula,
> msd-to-moduli, newtonian-limit-check]` — three MS-shaped files. This is not a
> schema to negotiate; it is a field that already exists on both sides."*
>
> **Measured 2026-09-15 against `bd@a18e171`: 1 of 42 papers carries a
> `provides:` array**, and it is `mason-weitz-1995` — the one the paragraph
> cited. Across the whole of BD's `knowledge/`, exactly one file has the field.
>
> | Frontmatter shape | Papers |
> |---|---|
> | `type: source` | **40** |
> | `type: paper-distillation` | 1 |
> | `kind: literature` (carries `provides:`) | **1** |
>
> So the decomposition key does not exist on both sides, and *"not a schema to
> negotiate"* was the opposite of the truth. **This is the third time this plan
> has been argued forward by a fact nobody checked** — after §1.8's linters and
> §1.6's two machines — and it is the only one of the three that blocks work
> rather than adding it: v2's literature crosswalk was designed around the field.

**What BD holds instead is narrower and, in one way, better.** 11 of the 42
papers carry `parameters_extracted: yes`, and the extraction is in the **body**
rather than in frontmatter. `2008-park-salt-surfactant-interface-forces` §1
records `η_eff` with the page it came from (*"본문 p.1689, Materials and
Methods"*), the boxed expression, the surface-area-weighted derivation, three
limit checks, and a conditions table that says which numbers **are not in the
paper at all** (`η_oil`, `η_water`, the contact angles). That is closer to MS's
mandatory `## Transfer conditions` than a `provides:` array ever was — a list of
names does not say what has to hold.

**The crosswalk therefore has to read a section, not a field** — which is a
parser to write rather than a mapping to apply, and it is v2's work. What it is
not is a schema negotiation: both sides already record conditions, and neither
records them in a key the other can look up.

**And the first `kb/literature/` entry does not follow from this gap.** MS has
exactly two registry gaps — `data/fluorophores.yaml > lifetime_ns` (6 of 17
dyes, gate **G20**) and `data/particles.yaml > source` (4 of 8, no gate). The
first is a literature quantity and **BD holds no fluorophore data at all**: its
42 papers are colloid and active-matter physics. The second is a provenance
field, not a published number. So the sharpest gap in the *system* and the
first entry MS's folder can receive are not the same task, which this section
had treated as one.

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

### 1.6 One machine — and what the two-machine reading cost

> **Corrected 2026-09-15 by the operator, and it retires an argument this plan
> leaned on twice.** This section read *"the two repos run on different
> machines"* and concluded that a shared local filesystem could not be assumed.
> **BD running on macOS is a development environment, not a deployment
> target**: it passes CI and runs anywhere. **Everything runs on the
> microscope PC**, and separation waits until the system is understood well
> enough to be worth splitting (decision 35).

MS `.mcp.json`:

```json
"command": "C:\\Users\\<lab PC>\\venvs\\auto_microscope\\Scripts\\python.exe"
```

MS's MCP server holds hardware on the **lab Windows PC**, and that is where all
four systems run. Two facts survive the correction unchanged, and one argument
does not:

| | Status |
|---|---|
| The hard-coded absolute interpreter path above | **Still a fact, still the thing decision (i) has to replace.** One machine does not make an absolute venv path portable across the four `.mcp.json` files |
| `git fetch` as the ingest channel | **Unchanged.** All four repositories are public, the SHA becomes the index's provenance, and ingest never depended on where the clone sits |
| *"A shared local filesystem cannot be assumed"* | **Retired.** It can be assumed — there is one disk. §3.4 and Phase 5 both rested on it, and both are corrected below |

**The correction makes the design smaller, not larger**, which is why it is
recorded here rather than absorbed quietly: the always-on service was never
wanted for itself, only forced by a second machine that is not there.

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

> **544 was the first scan's figure, and it was not the only one.** §1.1 and the
> README both gave **513** indexed rows for the same 59 files at the same
> commit, and `librarian.index.build` filters nothing — it inserts every
> document the scan produced — so at most one was ever right.
>
> **Re-measured 2026-09-09, and the answer is that the question expired.** The
> microscope has moved to `fbedef0`, where the four adapters produce **554
> documents from 68 files** — it grew a `kb/sessions/` folder, three decisions,
> two expertise entries and a calibration. So neither historical figure
> describes the corpus, the disagreement between them is now unresolvable
> without checking out `196cdf1`, and nothing downstream depends on which was
> right. §5.1's *495 of 544* and `profiles/README.md`'s *544 real documents* are
> derived from that same expired scan and are read as historical.
>
> **This is `index_stale` applied to the plan itself** (§8, row 2). The lesson is
> not that a number was wrong; it is that a count written beside a tool that can
> compute it decays silently, so `adapters/README.md` now prints the command
> above the table.

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

### 3.3 The librarian is a server, not a fourth agent

Decided 2026-09-09.

The other three are conversational agents — a session, a context window, a model
that reasons. **This one is deliberately not a fourth,** and the reason is
mechanical: an LLM call is **stateless**, and the store is precisely the thing
that has to be remembered between calls. A librarian that reasoned would reload
its own system prompt and its own description of the corpus on **every
request**, which is the context cost the index exists to remove.

So there are two layers, and only the lower one is the librarian:

| Layer | What it is | Cost per call |
|---|---|---|
| **The store** | `kb/` · `index/kb.sqlite` · the adapters — deterministic code, no model | **zero tokens** |
| **The tool surface** | the nine MCP tools (§5.2) | the caller's tokens: the specs once per session, then a hit's text per call |

**"Retrieval that knows who asked" is therefore parameter design, not
judgment.** The caller's role arrives as `caller_profile` and the narrowing
happens **server-side against a versioned file** (§5.1) — not as a model
inferring what the caller probably meant. That is what makes the same question
under two lenses *reproducibly* different rather than differently guessed, and
it is the same argument as §3.2's against embeddings: a filter that cannot be
read off a file cannot be defended afterwards.

**A model may be called from inside a tool, and in v1 none is.** If a question
ever needs several sources reconciled rather than ranked, that call belongs
inside a tool implementation behind a named trigger condition — never a resident
agent, and never a source of numbers (§3.1 invariant 3, decision 24).

### 3.4 Transport and lifetime — three conditions, not one

*"The librarian can be called whenever an agent needs it"* is three separate
claims, and each fails differently.

| # | Condition | How it fails |
|---|---|---|
| 1 | **The server is running** | stdio dies with the session that spawned it; an HTTP service is unreachable while it is down. **No MCP client manages a server's lifetime** — uptime belongs to systemd, docker or a supervisor, not to the calling agent |
| 2 | **It was registered when the session started** | `.mcp.json` is read at startup, so the candidate set is **closed** for that session. Adding a server mid-session is a separate approval step, not a call |
| 3 | **Then it may be called freely — but every call is independent** | Request-response, no memory between calls. Anything that has to survive two calls is in the index, or it does not exist |

**The transport was settled by §1.6, and §1.6 was wrong.** The argument ran:
MS on the lab Windows PC, BD on macOS, no shared filesystem, therefore
stdio-per-session cannot accumulate anything shared, therefore an always-on
service. The premise is retired — BD's macOS is a development environment and
**all four systems run on the microscope PC** (decision 35). So:

| | stdio, spawned per session | one always-on service (HTTP/SSE) |
|---|---|---|
| Setup | nothing beyond `.mcp.json` | a host, a supervisor, a port |
| Knowledge accumulates | yes — across sessions on **one** machine, which is now the deployment | yes, across machines — **and there is no second machine to reach** |
| Concurrent writers | undefined: two spawned processes, one file | the service serializes, once it is written to |
| Lifetime | the session's | independent, and has to be watched |

**Read down the stdio column: one machine is what that column was always right
for.** `mcp_server/server.py` runs `transport="stdio"`, and the thing that was
going to force it out — the second machine — is not there. **stdio therefore
stays correct through BD**, which is the opposite of what this section said
until 2026-09-15.

**What had to be settled was the third row, and only that row.** Several
agents on one machine means several spawned processes over one SQLite file.
Reads are safe and concurrent — the server opens the index **read-only and per
call** (`mcp_server/tools.py`), so a rebuild is picked up on the next call and
no session holds a stale handle. Writes were *undefined*, and they were the last
forcing function for a service.

**Decision 36 closed that row without one** (§3.7): no write tool updates a
record, so nothing contends, and a record arrives by `os.link` from a complete
temp file — idempotent under retry, atomic under concurrent read. So **nothing
in this design now requires a service.** The shared registration form is still
decision (i): one machine does not make MS's absolute interpreter path
portable.

**And the tool surface is a budget.** Every registered tool's name and parameter
descriptions load into the **caller's** context at session start, in every
session, used or not — and prompt caching amortizes the repeat, not the first
load. That is a second reason a new question becomes a **parameter** of an
existing tool before it becomes a tenth tool (decision 25).

### 3.5 People are the second class of caller

Decided 2026-09-09; the host corrected 2026-09-15. The server runs on the
**microscope PC** (decision 35), and what reaches it there is not only the three
agents: a person asks in their own words, and the answer should fit who asked and
what for. **The host changes where this is urgent, not whether it is true** — a
person at that PC is still a second class of caller, and ② below is the one item
the correction genuinely defers.

**Three things that deliberately do not change.**

| | Why it holds |
|---|---|
| **No model inside the server** | A person arrives through **their own MCP client**, and that client's model composes the answer. The librarian still returns nothing but quoted text with coordinates and a tier — decision 24 stands and §3.3's argument is untouched |
| **The same nine tools** | A person's question is a `kb_search` under a different profile, not a tenth tool (decision 25) |
| **One transport, whatever it is** | A person's client registers the same server the agents do. §3.4 now keeps stdio through BD, so this is one line in one more `.mcp.json` rather than a host to stand up |

**And four things that do.**

**① The profile namespace.** People are keyed by **role and purpose, never by
person**: `human:*` files in `profiles/`, plus a `purpose` argument on the query.
Same file form as the lens profiles, same versioning, applied server-side the
same way (§5.1) — a role is *declared*, not inferred from the question. Two
reasons it is not `person:<name>`: profiles would then multiply with people
rather than with kinds of question, and a person-keyed profile records **who was
looking for what** in a public repository (§6.1).

**② `caller_profile` becomes an identity claim — and this is the part the
single-machine correction defers.** Among trusted agents on one machine a
self-declared profile is harmless: a wrong one is a bug in a config file. The
claim only becomes load-bearing on an endpoint several people reach
independently, and with everything on the microscope PC there is no such
endpoint yet — a caller is either one of the three agents or someone sitting at
that PC. So decision (l) stands open and **its trigger moves with the
separation** (decision 35), not with BD's arrival. What does not change is the
shape of the failure when it comes: a wrong role returns evidence that is
plausible, correctly cited and **not what that person needed**, and nothing in
the answer says so.

**③ The publish gate widens.** §6.1 already keeps raw query text off a public
path, because what someone searched for is what they are about to do. A person's
question in their own words is more revealing than an agent's, so human queries
fall under the same gate — and ① is part of the defence: role-keyed profiles put
no names in the log.

**④ `searched_empty` has to survive being read by a human.** A model that takes
zero results for a broken tool routes around it, which is why the server's
instructions say otherwise; a person takes it for *"the librarian does not
know"* and stops. The distinction from `not_searched`, and `kb_gaps`'s answer —
**which input is missing** — are what turn an empty result into a usable answer
instead of a dead end. That is §0.2①'s product, pointed at a person.

### 3.6 The four agents are themselves in the corpus — and what that licenses

Decided 2026-09-09. `map/04-agents/` already holds the structure and function of
each (sub)agent: MS's five lenses with their owned gates and declared tools land
there today through `adapters/ms_agents.py`, BD's nine agents in v2, RT's two
personas in v3. Two things are added here — a slot for the **fourth repository**,
this one, and the limit on what routing may do with any of them. §3.3 is
untouched by either: what enters the map is this repository's profiles and tool
surface, not a persona it does not have.

**The fourth slot is not another `.claude/agents/` read.** This repository has no
`.claude/` directory at all. Its role declarations are `profiles/` — who may ask
what, and how it is weighted — and `mcp_server/`'s tool surface with its
instructions, which fix what may be answered. So `map/04-agents/lib/` is
generated from those two, not from agent files that do not exist. That the four
repositories declare their agents in **four different kinds of file** is the
reason the map is a generated layer rather than a naming convention: it is where
the four forms are made comparable.

**What the map licenses is the correspondence, not the choice.**

| The librarian may | The librarian may not |
|---|---|
| report which lens declares `G10`, which agent owns `power_at_sample_mw`, which persona defines a pass condition — each read off an agent file at a locator | decide which lens a question belongs to |
| return the **candidate** profiles for a term, each with the declaration that made it a candidate | compose a profile, or silently apply one it inferred |
| route a challenge by the **type** of its falsifier — a measurement to MS, a run to BD, a condition of validity to RT (§5.2) | route by who sent it, or by what the answer would turn out to be |

The line is §5.1's and it does not move: **`caller_profile` is a declared
parameter, not an inference.** *"Judging better from each subagent's role"* means
the correspondence between a term and its owner is **in the index and therefore
citable** — `G10` belongs to lens 5 because `.claude/agents/` says so, at a
locator — not that a model guesses which lens the asker meant. A guessed profile
changes which evidence comes back (§3.5②) and **nothing in the answer shows that
it was guessed**, which is the same objection §3.2 raises to embeddings.

**Owner is an end of `kb_supplies`, not a tenth tool.** *"What supplies this
field"* and *"who owns it"* are one question asked from two ends, which is the
shape that tool already has (decision 25).

**And self-description is not self-confirmation.** `map/04-agents/lib/` records
which profiles exist and what each one weights. It does not let a retrieval
result change a weight: the loop [FEEDBACK.md](FEEDBACK.md) §5 blocks is a
*result* promoted to ground truth, and a weight changes only by an edit to a
versioned file, with a human in the diff.

---

### 3.7 Concurrent writes — none of the three mechanisms, and why

Decided and built 2026-09-15; closes open (j). **`librarian/record.py`.**

(j) offered a single-writer queue, a lock, or version-and-merge. All three
answer *"what happens when two writers want the same thing"*, and **no write
tool here wants the same thing.** `kb_challenge_raise` issues a challenge and
`kb_feedback` records a session; both emit a **new record** and neither updates
one. Custody already models a correction as a new record that supersedes the old
(`superseded_by`, edge 4) — so there is no update to lose and nothing to merge.

**The index is not written by a tool at all.** `build()` is a full rebuild from
a CLI invocation, never incremental, and every read tool opens the index
**read-only and per call**. So the contention (j) was written against does not
exist between tools; what is left is two narrower failures, each closed by
construction rather than by serialization.

| The failure | What closes it |
|---|---|
| A **retried call landing twice** | The filename is a sha256 of the canonical record. The same record gets the same name, the name is created exclusively, and the second write is an idempotent no-op reporting `created: false` |
| A reader seeing **half a record** — §8's *"an index built over a half-written entry"* | The bytes go to a sibling temp file and the final name is created as a **hard link** to it. `os.link` is atomic *and* exclusive in one call, so the record is absent or whole, never a prefix |
| Two **concurrent rebuilds** | Nothing, and nothing is needed: a rebuild is deterministic — sorted by `uid`, no timestamps (BUILD.md §4-A) — so identical inputs give byte-identical output and the race has no losing outcome. Differing inputs leave the last writer's index, and `index_stale` reports the truth on the next call |
| Two writers appending to a **generated rollup** | **There is no rollup, by decision.** This is the one shape that would need a lock, and it is also BD's `knowledge/source/papers/INDEX.md` — headed *do not edit by hand*, naming a generator not in the repository, stating 40 entries where 42 files exist (§1.2). The listing is derived at read time |
| `git` | Not in any tool's write path. Committing is a human or CI act, which keeps the worst contention out of the question entirely |

**Idempotence is load-bearing, not tidiness.** Oracle promotion requires a
session reproduced under **two distinct `index_sha`**
([FEEDBACK.md](FEEDBACK.md) §5, decision 21), and that condition exists to stop
an agent promoting its own retrieval results to ground truth. If a retried
`kb_feedback` could land twice, one caller calling twice would satisfy a check
built to need two index states — the damping on `C-001`'s loop would come off
through a retry.

#### Two mistakes the concurrency tests found, both worth keeping on the page

**① Claiming the name first defeats the thing it protects.** The first version
created the final path with `O_CREAT | O_EXCL`, then wrote the temp file and
renamed over it. That is exclusive, and it publishes an **empty file** for the
length of the write: a reader scanning then got `JSONDecodeError` on a name
already visible. Exclusivity and atomicity had to arrive in the *same* call,
which is what `os.link` does and what `O_EXCL` plus a later rename cannot.

**② A pid is not unique, and it caught the same error twice.** Both temp names
were `.{name}.{pid}.tmp`. Two **threads** of one process then share one temp
path: for a record they overwrite each other's bytes under it, and for the index
the second `sqlite3.connect` to a database the first is writing fails with
*attempt to write a readonly database*. Both carry a uuid now. The tests that
found it run real threads rather than reasoning about the code, which is the
only way either would have shown up.

**What this closes beyond (j).** §3.4 named two forcing functions for an
always-on service: a second machine, and a second writer. Decision 35 removed
the first; this removes the second. **Nothing in the design now requires a
service** — `demo/` keeps the HTTP transport as a contingency, not a plan.

**What it did not close.** The `publish-gate` scope for `sessions/` is a
disclosure question, not a concurrency one — a record written perfectly is still
a record of what someone was looking for. Settled separately, §6.1,
decision 37.

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

Three tables sit beside it, all derived at build time so the MCP server has one
dependency rather than two — a query-time check against the source tree would
compare against a repository that has moved while the index has not.

| Table | Holds | Read by |
|---|---|---|
| `link` | every cross-reference, with `status` = `indexed` · `in_repo` · `missing` | `kb_neighbors`, and the broken-reference finding |
| `gap` | registry coverage per (registry, entry, field) | `kb_gaps` · `kb_supplies` |
| `finding` | the §4.3 drift report | `kb_stale` |

> **`status` on a link is three-valued for a reason.** A reference to
> `../../NOTICE.md` resolves to a file that exists and that no adapter reads —
> `in_repo`, and not a defect. Only `missing` is one. Collapsing the two reports
> the whole reference graph as broken, which is how a link checker becomes noise.

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

Later: `ms:lens-{3,6,8}` (v1, if useful) · `bd:s1`–`s8` · `bd:lit-*` and the
`human:*` role profiles (v2, §3.5) · `rt:V1` · `rt:V2` (v3).

### 5.2 Nine tools

Seven read, two write. **Writes touch `kb/` and `store/` only.** The surface is
held at nine for the reason in §3.4 — every registered spec is loaded into the
caller's context at session start, so a new question becomes a parameter of one of
these before it becomes a tenth tool.

| Tool | Signature | Returns |
|---|---|---|
| `kb_search` | `(question, caller_profile, limit?, require?)` | hits with `repo@sha:path#locator`, `evidence`/`tier`/`advances`, `has_falsifier`, and `index_stale`. Zero results is **`searched_empty`, distinct from `not_searched`** (constraint ①). Terms of 3+ characters go to FTS5 `MATCH` (bm25-ranked, OR-combined); shorter ones to `GLOB` → [BUILD.md](BUILD.md) §3. Also `profile_candidates` — which profiles declare the question's terms, each citing the agent file that declares it, and **applied to nothing** (§5.3) |
| ✅ `kb_get` | `(uid)` | body, full frontmatter, and both link directions. A missed locator returns `not_found` **with the other sections of that path**, because the usual cause is an edited heading |
| ✅ `kb_neighbors` | `(uid, relation, direction)` | `cites` · `supersedes` · `superseded_by` · `applies_to` · `same_file`. A neighbour's `status` separates *indexed* from *exists but unindexed* from *absent* |
| ✅ `kb_inputs` | `(computation)` | **the scalar closure of a function's signature**, each leaf resolved to a registry field with its coverage, to a recorded alias, or to ranked candidates. The question *"what do I need to compute X"* is not a search, and no ranking reaches an answer that is a closure |
| ✅ `kb_supplies` | `(field \| gate)` | what supplies that registry field, or what a gate waits for — the same question from either end. **`bleach_photons` × G10 returns `blocked`** |
| `kb_gaps` | `(caller_profile)` | gates `BLOCKED` for want of an input · registry fields still empty · `has_falsifier = 0` entries. **v1's primary product** (§0.2①) |
| ✅ `kb_stale` | `()` | staleness **and** the §4.3 drift report, both stored in the index at build time so the server needs the index and nothing else |
| ✅ `kb_challenge_raise` | `(target_uid, doubt_kind, falsifier_cited, caller_profile?, note?, gpu_hours?, instrument_hours?, search_budget_spent?, in_reply_to?)` | writes `store/challenge/` and **routes by falsifier type**. `falsifier_cited` is mandatory *and* must share the target's file — a citation elsewhere is `T-048`'s prohibited move. `routed_to`, `resolvable_by`, `state`, `raised_by` and `depth` are **derived, not parameters**, because a caller that could set them would be routing by the sender |
| ✅ `kb_feedback` | `(query, caller_profile, verdict, returned?, cited?, missing?, asked_by?, action?, note?)` | writes one session to `kb/08-retrieval/sessions/`, local and never committed. `index_sha`, `index_stale` and the id are **derived, not parameters**. Refuses `not_searched` — that is the default of a query nobody recorded, and the call is the record that someone looked. Returns `promotion_status`, which promotes nothing → [FEEDBACK.md](FEEDBACK.md) |

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

### 5.3 Profile candidates — the caller chooses, and the reason is citable

Decided 2026-09-15. **Built the same day** — `Index.profile_candidates`,
returned by `kb_search` and printed by `librarian search`. Two things changed
between the design above and the working version, and both are recorded at the
end of this section rather than smoothed out of it.

§5.1 makes `caller_profile` a declared parameter and §3.6 forbids inferring it.
Both stand. **What neither supplies is how a caller who does not already know
which profile to declare finds out.** Today `kb_search` under an unknown profile
returns `unknown_profile` with `available` — a list of ids and nothing to choose
by, which leaves the whole burden on the caller knowing the corpus before it
queries the corpus.

The proposal this answers was a resident model on top: read the question,
understand the asker, pick the profile. That is decisions 23 and 24 again and the
grounds have not moved — a reasoning librarian reloads the corpus description on
every request, and a guessed profile changes the evidence returned with nothing
in the answer marking it as guessed.

**What is allowed is already written down.** §3.6 licenses returning *the
candidate profiles for a term, each with the declaration that made it a
candidate*. The shape exists too: `kb_inputs` already answers an unresolved leaf
with `candidates` plus `candidate_query` — *"a weaker answer than the question
asked, and an honest one"* (`librarian/inputs.py`). This is that pattern one
level up.

**A return field of `kb_search`, not a tenth tool** (decision 25):

```text
kb_search(question, caller_profile="neutral")
 -> hits:            [...]           # the declared profile's, and applied
    applied_profile: "neutral"
    profile_candidates:
      - profile:  "ms:lens-5-photo-perturbation"
        because:  "ms@9f971a8:.claude/agents/photo-perturbation.md#owns"
        declares: "Light level, illumination duty, total dose, wavelength choice"
      - profile:  "ms:lens-4-sample-optics"
        because:  "ms@9f971a8:.claude/agents/sample-optics.md#owns"
        declares: "Objective choice, immersion, coverslip thickness, chamber"
    candidates_applied: false
```

**Five rules. The third and fifth were found by building the ground for it.**

1. **Nothing is applied.** The hits are the profile the caller declared. A
   candidate is information, not an action — and the caller's pick then lands in
   the **caller's own** transcript, where it is visible. That is the whole
   difference between this and a guess.
2. **The reason cites the agent file, never the profile.** §3.6: self-description
   is not self-confirmation. `profiles/*.yaml` is this repository describing
   itself; the licence to say lens 5 owns a term is MS's `.claude/agents/`, at a
   locator.
3. **The key is `owns`, not gate ownership.** Measured 2026-09-15: **only 3 of
   MS's 5 agent files name a gate in their own description** —
   `measurement-validity`, `mechanical-env`, `sample-optics` — so
   `adapters/ms_agents.py` emits a `gates` locator for those three and for
   neither of the other two. **Lens 5 is one of the two, and it is also one of
   the two v1 profiles**: it named exactly one gate, `G10`, and MS removed G10 on
   2026-09-09. Keyed on gates, this mechanism returns no candidate for the lens
   the corpus is best prepared for. All five files carry `owns` and
   `definition`, both already indexed as `kind=agent`, and `definition` holds the
   invocation clause MS wrote for exactly this purpose — *"Invoke it when the
   user mentions photobleaching, phototoxicity, light-driving …, exposure dose,
   or illumination intensity."*
4. **A profile with no agent file gets no candidate.** `human:*` (§3.5) and
   `lib/` have none. An empty candidate list is the right answer there, not a
   reason to relax rule 2.
5. **Match over the index, never over the profiles' own lists.** Those lists were
   read off **code** — each profile header says so — and the index covers `kb/`,
   `data/`, `docs/` and `.claude/agents/` and **no Python at all**. A term named
   only in a module is inert by construction, and four of the eighteen boosted
   field terms were: `design_coverslip_um` and `resolved_slab` (lens 4),
   `dose_limit_j_cm` and `resolved_irradiance` (lens 5). `Profile.score` matches
   a boosted field as a **substring of a document's title, body and
   conditions**, so a term no document carries can never raise anything. Removed
   2026-09-15, each with its reason left in the file.

**A profile is a claim about another repository, so it goes stale.**
`ms-lens5-photo-perturbation.yaml` boosted `G10` for six days after MS deleted
the gate and **nothing caught it**: `librarian/drift.py` reads MS's `docs/`
against MS's code and never reads this repository's own files. That is the one
place a dead identifier could sit unnoticed, and it is load-bearing here — an
owner list naming a retired gate is a wrong answer **with a citation attached**,
which is the single kind of output this design exists to prevent.
`tests/test_profiles.py` now checks all three lists on every run: gate ids
against the gates MS's code declares, field terms against what the index can
actually match, and `kind_weight` keys against `librarian.doc.KINDS`.

**Two strengths, because the two kinds of term fail differently.** A retired gate
stays in prose — `docs/04` §6 keeps G10's formulas and explains the removal — so
corpus presence would not have caught it, and gate ids are checked against code
instead. A field is the reverse: `n_medium` is declared by no registry
(`optics/components.py` computes it from a lookup keyed by one) and lens 4 is
right to boost it, so what is checked there is only whether the boost can ever
fire.

**What this does not do.** It does not rank candidates against each other beyond
the retrieval score that produced them, it does not compose a profile (§3.6), and
it settles nothing about **owner**, which stays an end of `kb_supplies` rather
than a tenth tool (decision 25, open (n)).

#### What building it changed

**① Matching the question the way `search` does it made the mechanism useless.**
The design said *"match the question's terms against those rows using the same
FTS path, so why a hit matched is answerable in coordinates."* Done literally —
one OR-combined query — it ranked *"how long can I image this dye before it
bleaches"* under **lens 4** and *"what seed did that run use"* under lens 5.
Over 1,446 documents bm25 and the profile weights hold function words down.
Over **five** agent files they do not: `how`, `this` and `run` occur in all five
declarations, because an `owns` section is prose. So each term is now asked
separately, under two rules:

| Rule | Effect |
|---|---|
| A term matched by **every** owner is dropped | It states nothing about which owner. Vacuous where there is only one owner, and it must not fire there — it did, and no candidate could be produced against a one-lens index at all, a boundary the five-lens corpus hid completely |
| A candidate needs at least one term with **exactly one** owner | §3.6's sentence as arithmetic: *"report which lens declares `G10`"* is answerable because `G10` has one owner. The same sentence about a term every lens declares would be true and useless |

A function-word list (`_STOPWORDS`) does the rest, and **it is not the
morphological analysis decision 7 rules out.** That rules out a stemmer, on the
grounds that reproducibility outranks ranking quality; a fixed list in a
versioned file is a stemmer's opposite — readable, diffable, identical on every
machine. It is consulted for candidates only. `search` never sees it, because
the hits are the product this repository is judged on.

**② An inflected word does not reach the declaration, and the honest result is
an empty list.** `_fts_expr` quotes a term as a phrase, so trigram matching
needs a contiguous substring: **`bleach` finds `photobleaching` in 14 agent
documents and `bleaches` finds 0.** Decision 7 rules out the stemmer that would
bridge them, so the inflected question returns **no candidate** — while *"how
much bleach dose can this dye take"* returns lens 5 at 1.00.

That is a limit, and it is the right one to have. Before the two rules above,
that same question *did* return lens 5 — licensed by `can` and `this`. The right
owner for a reason that says nothing is worse than no owner, because a cited
suggestion reads as evidence. `tests/test_profiles.py` pins both, so the
tempting fix — loosening the match until `bleaches` lands somewhere — fails
rather than passes quietly.

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
looking for is what they are about to do.**

**Settled 2026-09-15, decision 37; closes open (a).** `librarian/publish.py`.
Of the three options open (a) offered, one was already foreclosed and one was
never safe:

| Option | Settled as |
|---|---|
| Hash the query only | **No.** Decision 3 in [FEEDBACK.md](FEEDBACK.md) keeps the raw query because it is the reproduction input, and §3 there is why that matters: retrieval has no grader, so a past confirmed citation stands in for one. Hashing makes an oracle unrunnable — it trades the whole purpose of the folder for a protection the folder split already gives |
| Commit as-is | **No.** rt `T-019`①: in a public repo, deleting the file afterwards does not undo the disclosure. And no human reads a session before it lands |
| **`sessions/` local, `oracles/` committed** | **Yes — and not provisionally.** |

**The reason it is not merely a folder split is that the split lands on a human
approval that already exists.** An oracle *is* `(query, caller_profile) →
cited`; it carries the raw text by definition, so committing `oracles/` does
publish query text. What makes that safe is that **promotion is human-approved
already** ([FEEDBACK.md](FEEDBACK.md) §5, decision 21) — put there to block the
self-confirming loop, and it happens to be the exact moment a person reads the
query text and can judge whether it publishes a direction. The gate needed no
new ceremony; it needed the existing one named.

Three consequences, each checked rather than asserted:

- **`sessions/` is gitignored permanently.** A session accumulates
  automatically and volume guarantees no one will review them, so the default
  is safety — the same habit as `not_searched` being the default.
- **A `findings/` record carries no raw query.** Its own folder is *"why a
  profile fails — the cause, not the symptom,"* and a quoted query is the
  symptom as well as the disclosure.
- **No record in either folder names a person.** `asked_by` is a role (`agent`,
  or a `human:*` profile), never a name — rt `T-018` · `T-035`, *citations stay
  and attributions go*, and decision 29 for the same reason.

**The cost, stated rather than discovered later: a query that reveals a
direction cannot be promoted.** It stays a session — a usable regression check
for whoever holds it locally, and one CI will never run. That is a real hole in
coverage and it is the right side to err on, because the alternative is
unpublishing something that cannot be unpublished.

`tests/test_publish_gate.py` asserts the `.gitignore` and
`librarian/publish.py` agree. A rule that lives in one and is contradicted by
the other is worse than neither, because it reads as a guarantee — and
`kb/08-retrieval/sessions/*` and `kb/08-retrieval/*` are one character apart,
the second of which silently stops committing the oracles.

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
| ✅ **`kb_inputs`** | For `radial_stiffness_n_per_m`, returns `blocked` with `power_w` unresolved and the objective list `6/6` ready — a closure taken from the signature, not a hand-written input list |
| ✅ `kb_get` · `kb_neighbors` · `kb_supplies` · `kb_stale` | Seven read tools, all annotated read-only |
| ✅ MCP server registered | `.mcp.json` at the root, `python -m mcp_server.server`. **Not `mcp/`** — that directory name shadows the SDK, and `python -m` puts the working directory first on `sys.path`, so the failure appears only from inside the repository |

### Phase 2 — interlocks (**before** any KB content)

| Task | Exit condition |
|---|---|
| `librarian reindex` + `index_stale` | A stale index cannot answer silently; `--strict` refuses |
| Regeneration | Delete `index/` and `map/` entirely, rebuild, **byte-identical** |
| ID issuance | `kb-schema.md` §6's *"who issues entry IDs — sequential numbers collide under parallel writes"* → **content-hash**, inheriting BD's `run_id` approach. **Done** — `librarian/record.py` names every record by a sha256 of its own content, and `ret-`/`chal-` ids are read off the filename rather than stored inside it (§3.7) |
| `publish-gate` (§6.1) | A write of unpublished content to a public path is blocked, **proved by a test** |

### Phase 3 — the first entry, and feedback

| Task | Exit condition |
|---|---|
| `kb/literature/` first entry | Every mandatory section of MS `_template.md` filled; merged into MS as a **pull request** |
| `kb/08-retrieval/` — the write half | **Built 2026-09-15.** `kb_feedback` and `librarian/feedback.py`: one session per call, local and never committed, every rule in [FEEDBACK.md](FEEDBACK.md) executable rather than prose |
| `kb/08-retrieval/` — the exit condition (**F9**) | **Met 2026-09-15.** `librarian/oracle.py` + `tests/test_oracle.py`. The first oracle came from two real sessions — the same citation recorded under `ms@196cdf1` and `ms@9f971a8`, reached by rolling the clone back and rebuilding — and from the operator supplying the two assertions no code can: that the result is an oracle, and that its query may be published. Breaking `ms:lens-4-sample-optics` then turns it red on the real corpus |

### Phase 4 — migration

→ [BUILD.md](BUILD.md) for the acceptance gate, [MIGRATION.md](MIGRATION.md) for
the five steps. **Deletion is Step 5.**

### Phase 5 — the second writer, and the second kind of caller

**Retitled 2026-09-15.** This phase read *"the second machine"* and everything
in it waited on BD, because a second machine was what forced a service. There is
no second machine (§1.6, decision 35), so what is left here waits on the
**second writer** instead — and that arrives from concurrency on one machine, not
from a platform.

| Task | Exit condition |
|---|---|
| ~~One always-on service on the lab NAS~~ | **Dropped** (decisions 35 and 36). stdio stays correct through BD, and writes turned out to need no serialization — so a service returns only when the separation begins, if then |
| The shared registration form (decision (i)) | One line, valid in all four `.mcp.json` files and in a person's client, with no absolute interpreter path in it |
| `human:*` role profiles + `purpose` (decision 29) | A person's question and a lens's question return **different** top results from the same corpus, the way the lens pair already does ([BUILD.md](BUILD.md) §4-B) |
| `map/04-agents/lib/` (decision 30) | Generated from `profiles/` and the tool surface, and a query for a term reports **which** profile declares it, with a locator — never which profile the asker meant (decision 31). The mechanism is §5.3's `profile_candidates` |
| ~~A second writer (decision (j))~~ | **Done** (decision 36, §3.7). Its exit condition was *"two concurrent writes leave the index in a state a full rebuild reproduces exactly"* — met by making the rebuild atomic and deterministic rather than by serializing anything, and asserted under real threads in `tests/test_record.py` |

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
| **Unpublished direction goes public** | Query text or a digest in a public repo | **Closed by decision 37** (§6.1). `sessions/` is gitignored permanently; raw query text is committed only in `oracles/`, where a human approval already stands between the record and the commit. `librarian/publish.py` declares the boundary and `tests/test_publish_gate.py` asserts the `.gitignore` agrees — the failure mode of a rule kept in prose only |
| **Rank becomes worth** | A score stored in an entry | §2.1 — returned, never stored |
| **The server is unreachable** | Every call errors — or, worse, the tools are absent from the session and nothing says so | §3.4's three conditions. Uptime belongs to the host, not to a caller; and a caller that could not reach the store records `not_searched`, which is a fact, rather than nothing |
| **Two agents write at once** | A lost update, or an index built over a half-written entry | **Closed by decision 36** (§3.7): no write tool updates a record, so there is no update to lose, and a record arrives by `os.link` from a complete temp file, so a reader never sees a prefix. The index build is atomic for the same reason. `tests/test_record.py` asserts both under real threads |
| **A person is served under the wrong role** | A plausible, correctly cited answer that is not the one they needed — and nothing in it says so | Roles are versioned files, so a wrong answer is at least reproducible and diffable. Whether the service checks the declared role is decision (l) (§3.5②) |
| **The librarian infers a profile** | Retrieval narrows to a lens nobody asked for, invisibly | §3.6: the agent map supplies the correspondence, the caller makes the choice (decision 31) |
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
| 15 | `runs/` (227 records in 256 directories) | **Not migrated**; indexed only | Run provenance is BD's (`charter.md` §3) |
| 16 | `tools/kb.py` | **Retired** | Its `ENTRY_DIR` returns 0 silently |
| 17 | Broken-reference CI check | **Required at MIGRATION Step 2** | The only defence against §8's last row |
| 18 | Weekly automation | **Deferred** → `index_stale` | Decided 2026-09-06 |
| 19 | `cited` collection | **Reported by the caller**, never inferred | Inferred, it stops being a fact |
| 20 | Missing feedback | **`not_searched`** | Constraint ① |
| 21 | Oracle promotion | Two distinct index SHAs **+ human approval** | Blocks the self-confirming loop ([FEEDBACK.md](FEEDBACK.md) §5) |
| 22 | Fixture disposal | **When MIGRATION Step 1 begins** | Otherwise the same entry exists twice |
| 23 | What the librarian **is** | **An MCP server over a deterministic store** — not a fourth conversational agent | An LLM call is stateless, so a reasoning librarian reloads the corpus description every request (§3.3) |
| 24 | An LLM inside a tool | **None in v1.** If ever, inside one tool behind a named trigger — never resident, never originating a number | A resident agent reintroduces the per-request context cost the index exists to remove (§3.3) |
| 25 | Growing the tool surface | **A new question becomes a parameter before it becomes a tool** | Every registered spec is loaded into the caller's context at session start (§3.4) |
| 26 | v1 transport | **stdio, one process per session** | One repository, one machine, one writer, no tool that writes (§3.4). **Revised 2026-09-15:** it does not stop at BD either — the second machine that was going to force a service does not exist (decision 35) |
| 27 | ~~Host for the always-on server~~ | ~~The lab NAS~~ — **superseded by 35** | Decided 2026-09-09 on §1.6's two-machine premise, and that premise was wrong. Kept rather than deleted: it is the second time this plan has been argued into extra machinery by a fact that was not checked (the first is §1.8's linters) |
| 28 | How **people** reach it | **Their own MCP client.** The server returns cited evidence; the caller's model composes the answer | No synthesis layer, so decision 24 and §3.3 stand unchanged, and there is one server to keep up rather than two surfaces to keep equal (§3.5) |
| 29 | Profile namespace for people | **Role and purpose** — `human:*` plus a `purpose` argument — **never per person** | Profiles multiply with kinds of question, not with people; and a person-keyed profile records who was looking for what in a public repository (§3.5①, §6.1) |
| 30 | The fourth agent in `map/04-agents/` | **`lib/`, generated from `profiles/` and the tool surface** | This repository has no `.claude/agents/`; those two files are where its roles are actually declared (§3.6) |
| 31 | What the agent map licenses | **The correspondence, not the choice** — report which lens owns a term; never infer the caller's profile | A guessed profile changes the evidence returned and nothing in the answer shows it was guessed (§3.6, §5.1) |
| 32 | **Whether Librarian ever calls a source repository** | **Never.** It is an MCP *server* and never an MCP *client* of MS, BD or RT. Ingest stays one-directional: `git fetch`, and the sha becomes every hit's provenance | Confirmed 2026-09-15. Calling out breaks all three of §3.4's conditions at once — an answer would depend on another agent's session being up — and a two-way call has no depth bound, so the loop circulates doubt instead of topics (`C-001`). Edge 4 stays a routed file drop |
| 33 | **How a caller finds its profile** | **Candidates returned with citations, never applied** — a return field of `kb_search`, keyed on each agent file's `owns`, with `candidates_applied: false`. **Built** `Index.profile_candidates` | Decided and built 2026-09-15, §5.3. Decision 31 forbids inferring the profile and says nothing about how a caller learns which to declare; this is that, without a model — the pick happens in the caller's transcript where it is visible |
| 34 | **Whether this repository's own files are drift-checked** | **Yes, by `tests/test_profiles.py`** — gate ids against MS's code, field terms against what the index can match, `kind_weight` against `KINDS` | Decided 2026-09-15. `librarian/drift.py` reads MS against MS and never read `profiles/`, so a profile boosted `G10` for six days after MS deleted the gate. An owner list naming a retired gate is a wrong answer with a citation attached (§5.3) |
| 35 | **Where everything runs** | **The microscope PC — all four systems, one machine.** Separation is deferred until the system is understood well enough to be worth splitting | Decided 2026-09-15 by the operator; **supersedes 27** and retires §1.6's two-machine premise. BD's macOS is a development environment, not a deployment target: it passes CI and runs anywhere. The consequence is subtraction — stdio stays correct through BD, the NAS host is dropped, and decision (j) becomes the only remaining reason to want a service |
| 36 | **Concurrent-write policy** | **None of the three offered.** Append-only records, named by a sha256 of their content, created by `os.link` from a complete temp file — idempotent under retry, atomic under concurrent read, and no rollup file for two writers to contend over | Decided and built 2026-09-15, §3.7; **closes open (j)**. All three mechanisms answer *"two writers want the same thing"*, and no write tool here wants the same thing. It also removes §3.4's second forcing function for a service, so after decision 35 **nothing requires one** |
| 37 | **`publish-gate` scope for `sessions/`** | **`sessions/` local only and permanently; `oracles/` and `findings/` committed.** No raw query outside `oracles/`, and no record names a person | Decided and built 2026-09-15, §6.1; **closes open (a)**. Hashing the query makes an oracle unrunnable (FEEDBACK decision 3); committing as-is cannot be undone (rt `T-019`). The split works because promotion is human-approved already, and that approval is the disclosure review — declared in `librarian/publish.py`, and the `.gitignore` is asserted to agree with it |

### Open — decided when the work reaches them

| # | Decision | Blocks |
|---|---|---|
| b | ~~`D:\data` access — run on the lab PC, or ingest a metadata export~~ | **Closed by decision 35**: the librarian runs on the microscope PC, so the acquisition archive is a local path. What remains is not access but volume, which is `envelope.sqlite`'s own problem (v2) |
| c | Indexing `D:\codes` (the analysis code lens 6 reads) | **No longer an access question** (decision 35) — it is now a scope question: the index covers no Python anywhere (§5.3 rule 5), and lens 6's analysis code would be the first (v2) |
| d | `entries/` (135) decomposition by `origin` | v2 |
| e | `export/` wiring — git subtree or generated commit | MIGRATION Step 3 |
| f | Tier 1 execution site | When the weekly job is built |
| g | Deletion timing | MIGRATION Step 4's proof |
| i | **One registration form every caller uses** — **a command, not a URL** now that decision 35 keeps the transport on stdio, and how each `.mcp.json` gets it | v2. MS's own entry hard-codes an absolute Windows interpreter path (§1.6), which is exactly what a shared form has to replace, and one machine does not make it portable — a person's client needs the same line (§3.5) |
| k | Whether the claim-extraction axes — `validity` · `durability` · `operational` · `controversy_id` — enter the index as columns | `kb_search`'s `require` parameter. None of the four exists in any of the three repositories yet; if they land they arrive **opt-in per query**, never as profile filters, for §5.1's reason |
| l | **Whether the service verifies a `caller_profile` claim**, or accepts it as declared | An endpoint several people reach independently (§3.5②). **Its trigger moved with decision 35**: not BD's arrival, but the separation — trusted agents and one operator on one machine never raise it |
| m | **The `human:*` role set** — which roles exist, and who writes them | the first caller who is not the author (§3.5①) |
| n | Whether **owner** becomes an end of `kb_supplies`, or `map/04-agents/` is read directly | routing from the agent map (§3.6) |

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
