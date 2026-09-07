# File tree

Drafted 2026-09-06 · status `draft` · supersedes [PLAN.md](PLAN.md) §0 of the
first draft

Librarian is the **fourth axis**: custody, retrieval and interaction for
knowledge. `research-topic` stays with proposal and validation. The practical
consequence is one thing — **Librarian owns the content.** The first draft only
indexed; this one holds the canonical store, and the tree turns on that.

**v1 is the microscope agent only.** All eight `kb/` folders are created;
`05` and `06` stay empty until v2 → [PLAN.md](PLAN.md) §0.

---

## 1. What the seven proposed categories already get right

The categories asked for were:

1. materials · 2. microscope hardware · 3. microscope software ·
4. structure and function of each (sub)agent · 5. physical phenomena ·
6. simulation · 7. key literature and books

Two of those groupings already match a distinction the two working repos reached
independently. Grounded boundaries are the ones that stay put, so the grounds are
recorded.

**① Separating `1 materials` from `2 hardware` is right.** It is exactly why MS
built `kb/samples/` — `docs/02-knowledge-base.md` §8:

> *"Knowledge attached to **what is being imaged**, not to a system. **It survives
> hardware changes.**"*

The axis dividing them is not subject, it is **lifetime**. Swap the objective and
2 changes while 1 stays. That makes it a checkable rule rather than a preference.

**② Keeping `7 literature` separate is right, but for a different reason** — not
subject, **copyright**. BD already solved this at folder level: `raw/` is
gitignored, only the distillation is in-git, and the handbook contract reads
`distillation#section ← [short-name] p.page`, so *a claim can be walked back to
the page it came from without the book being in the repository*.

---

## 2. Three structural problems with subject alone

### Problem A · Category 4 is a different kind of thing

`1·2·3·5·6·7` are knowledge about **the world**. `4 agent structure` is knowledge
about **the system itself**, and decisively, it is **derived** — a commit to any
source repo makes it stale.

| | 1·2·3·5·6·7 | 4 |
|---|---|---|
| Source | measurement · literature · experience | files in the three repos |
| Rate of change | months | every commit |
| Written by | humans and agents | the generator only |
| Editable by hand | yes | **no** |

Put them on one level and the refresh job has no good option: regenerate
everything and it erases what a human wrote; regenerate nothing and 4 rots.
**And that failure has already been observed** — BD's
`knowledge/source/papers/INDEX.md` is headed *do not edit by hand* and names a
generator, `docs/tools/wiki_index.py`, which is not in the repository. Its entry
count reads 40 against 42 actual files.

**→ 4 moves to `map/` (derived). The missing number 04 under `kb/` is the marker
for that rule.**

### Problem B · `5 physics` and `6 simulation` overlap

Is GSER (`knowledge/source/papers/1995-mason-weitz-gser-microrheology.md`)
physics or simulation? Physics — but simulation is what consumes it. With both
folders present it lands in one and is missed by a search of the other.
**That is BD's own "largest debt" — the `wiki/` vs `entries/` split — recurring
one level down, at the folder.**

One boundary rule settles it:

> **Swap the engine from HOOMD to LAMMPS. Does the entry change?**
> Yes → `06-simulation` · No → `05-physics`

GSER does not change → 05. The `Δt` gate, the non-dimensionalization convention
and the equilibration criterion do → 06. Because the rule is checkable, two
people give the same answer.

### Problem C · `3 microscope software` names three different things

| What | Where it actually lives | Where it goes |
|---|---|---|
| (a) **The instrument control stack** — MicroManager `.cfg`, the piezo command set, LUNF/DAQ | MS `config/micromanager/`, `reference/npcd-command-set.md` | **`03-control`** |
| (b) **MS's own agent code** — 8 gate modules, G1–G32 | MS `optics/`, `sample/`, `compute/`, … | **`map/04-agents`** (derived) |
| (c) **The analysis code** — `D:\codes` | outside every repo; only MS lens 6 reads it | **deferred to v2** (§6) |

(c) is the awkward one. MS `.claude/agents/measurement-validity.md` defines lens
6 as *"the only lens that also reads the analysis code (`D:\codes`)"* — so **code
that participates in a verdict is in none of the repositories.** Whether it gets
indexed is the same access question as the acquisition archive, so it moves with
it to v2.

---

## 3. The tree — the top level splits by write authority

Subject is the second layer. The top splits on **who may write**, because that is
the only axis deciding whether a file may be deleted and regenerated.

```
librarian-agent/
│
├── kb/                    ★ CANONICAL. Humans and agents write. Not regenerable
│   ├── README.md              the writing rules, and why 04 is absent
│   ├── 00-decisions/          decision log — chronological, not a subject
│   ├── 01-materials/          ← 1 materials
│   ├── 02-hardware/           ← 2 microscope hardware
│   ├── 03-control/            ← 3 microscope software (a: the control stack)
│   ├── 05-physics/            ← 5 physical phenomena          [empty until v2]
│   ├── 06-simulation/         ← 6 simulation                  [empty until v2]
│   ├── 07-sources/            ← 7 key literature and books
│   │   ├── papers/                one distillation per source, in-git
│   │   ├── books/                 distillation only
│   │   └── raw/                   ★ gitignored — originals never enter the repo
│   └── 08-retrieval/          ★ self-knowledge: what was asked, what was cited
│       ├── sessions/              one query = one formal object
│       ├── oracles/               promoted to regression tests (human-approved)
│       └── findings/              why a profile fails — the cause
│                              → schema and rules: FEEDBACK.md
│
├── map/                   ◆ DERIVED. Regenerated in full. Never hand-edited
│   ├── 04-agents/             ← 4 structure and function of each (sub)agent
│   │   ├── ms/                    5 lenses · 8 gate modules · G1–G32
│   │   ├── bd/                    9 agents · 6 skills · 4 rules · A1–A10   [v2]
│   │   └── rt/                    personas V1·V2 · J1–J3 · the boundary table [v3]
│   └── manifest.json          {repo: sha, built_at, doc_count}
│
├── index/                 ◆ DERIVED. Delete and rebuild loses nothing
│   └── kb.sqlite              FTS5 (trigram) + metadata
│
├── export/                ◆ DERIVED, outbound. Read-only copies sent back
│   ├── ms/                    what MS lenses reach with Read/Grep/Glob
│   └── bd/                    what BD reads offline                        [v2]
│                              → why this is needed: MIGRATION.md §3
│
├── store/                 ● PUBLISHED by Librarian
│   ├── challenge/             the retirement mechanism
│   ├── digest/<ISO week>/     weekly refinement output          [deferred]
│   ├── crosswalk/             BD paper → MS quantity, 1→N                  [v2]
│   └── inbox/                 LLM proposals awaiting human approval
│
├── profiles/              caller_profile YAML → PLAN.md §5.1
├── librarian/             the package: doc model · scan · gaps · drift · index ·
│                       links · archive · cli
├── adapters/              one parser per repo contract
├── tests/                 unit + integration; Phase 0's exit condition is asserted
├── mcp_server/            the MCP server (not `mcp_server/` -- that name shadows the SDK)
└── cache/                 gitignored — shallow clones of the three repos
```

**Code is not one of the four zones.** `librarian/`, `adapters/`, `tests/` and
`mcp_server/` hold code, which is versioned and reviewed as code. The four zones below
describe **data**, where the question is who may overwrite what.

**The four zones:**

| Zone | Mark | Written by | Deletable | Tracked in git |
|---|---|---|---|---|
| `kb/` | ★ canonical | humans · approved agents | **no** | yes |
| `map/` · `index/` · `export/` | ◆ derived | generators only | **yes** — the rebuild is canonical | **no** — only the READMEs and folder markers |
| `store/` | ● published | Librarian | no (it is a record) | yes |
| `cache/` | — | `git fetch` | yes | no |

**Derived output is gitignored, not committed.** Tracking a derived file invites
hand-editing it, and a hand-edited derived file outliving its generator is the
failure this project exists to catch. They rebuild byte-identically from `kb/`
plus a commit SHA, so history gains nothing by holding them.

> **That `map/`, `index/` and `export/` are deletable is the point of the design.**
> While that property holds, §2-A's decay — an artefact outliving its generator —
> is structurally impossible. Let a derived zone hold even a little canonical
> content and the property breaks, and at that moment it becomes BD's `INDEX.md`.

---

## 4. Inside a subject folder — all six the same shape

The second layer is **not** subject again. Subdivide by subject and a file that
belongs in two places appears, and that is where a taxonomy dies.

Divide by **how a thing is verified** instead, inheriting BD
`docs/03-knowledge-base.md` §2: *"six kinds, **because they are verified
differently**."*

```
kb/0X-<subject>/
├── _index.md          ◆ generated. Header carries generator path + SHA
├── cards/             ★ the canonical unit — one (subject × purpose) pair per file
├── evidence/
│   ├── measured/          measured here.  evidence: measured  → may advance
│   └── assumed/           literature or estimate.  evidence: assumed  → may not
├── findings/          Q→A with citations.  includes dead-end-<slug>.md
└── questions/         unanswered. Closed by status, never deleted
```

### Why `cards/` is separate from values

BD `knowledge/wiki/CLAUDE.md` shows this by measurement: **the
non-dimensionalization convention and the governing parameters are not fixed by
the system alone.** Within one lab the reference units split three ways — ABP ×
control takes `τ_r`, brush colloid × non-equilibrium contact takes `τ_D`, passive
tracer × transport takes `τ_D` with a different length. Its rule (translated):

> *"On meeting a pair with no card, do not improvise the non-dimensionalization."*

**A card owns the convention and the routing; it does not own values.** Values sit
in `evidence/` with a tier. Without the split, "what `dt` was used for this
system" has no source attached to it.

The card unit per subject:

| Subject | A card is |
|---|---|
| `00-decisions` | no cards — one decision per file, dated |
| `01-materials` | (sample system × observed dynamics) — ATPS PEG/dextran × interfacial relaxation |
| `02-hardware` | (instrument configuration × mode) — current-laser × optical tweezers |
| `03-control` | (control stack × task) — MicroManager dualcam × two-colour acquisition |
| `05-physics` | (phenomenon × regime) — microrheology × linear viscoelastic response |
| `06-simulation` | (system × purpose dynamics) — **BD's convention, unchanged** |
| `07-sources` | no cards — one distillation per source |
| `08-retrieval` | no cards — see [FEEDBACK.md](FEEDBACK.md) |

### Why the evidence tier is a folder, not just a field

Both repos already made it a folder. MS: `kb/calibrations/` (measured) versus
`kb/literature/` (assumed), with *"a value this lab has measured … **outranks
anything here**."* BD: `source/papers/` (publishable) versus `source/lab/`
(gitignored).

BD states the reason: **a disclosure boundary applies at folder granularity.**

And the cost of mis-tiering is on record — BD filed `T = 300 K` as tier 1
(measured) when it was a choice, propagating **−4 % to −14 % into every `τ_B`
downstream.** A single frontmatter line gets written wrong and goes unnoticed.
**A path does not.**

> The `evidence` field stays. The folder is not duplication but a **cross-check** —
> when path and field disagree, the index catches it ([PLAN.md](PLAN.md) §4.3,
> last row).

---

## 5. Acquisition data itself does not enter the tree

MS `docs/02` §6 records the scale: **2,343 archived acquisitions**, indexed as
`kb/envelope.sqlite` — designed there, and **not built**. The records live in
`D:\data`, outside the repository.

**Librarian does not store acquisitions.** Three things come in and one does not:

| Comes in | Where |
|---|---|
| The **index** of an acquisition (conditions, metadata) | `index/kb.sqlite`, inheriting MS's `envelope.sqlite` schema — **v2** |
| A **measured value** from it | `kb/0X/evidence/measured/` |
| An **interpretation** of it | `kb/0X/findings/` |
| Images, frames, raw arrays | **never.** Coordinates only |

Same reason `raw/` is gitignored, and BD applies the same rule: *the repository is
not a PDF archive.*

---

## 6. Decisions

| # | Decision | Value | Grounds |
|---|---|---|---|
| 1 | Category 3's name | **`03-control`** | "Software" names three things (§2-C) |
| 2 | `05` / `06` boundary | **the engine-swap test** | Checkable, so two people agree (§2-B) |
| 3 | Number 04 under `kb/` | **left empty** | The gap marks the write-authority split |
| 4 | Analysis code `D:\codes` | **deferred to v2** | Same access question as the acquisition archive |
| 5 | Korean filenames | **no — paths are ASCII** | BD's `entries/` filenames already broke on Korean slugs; NFC/NFD splits them across macOS and Windows |
| 6 | Does `01-materials` absorb MS `kb/samples/` | **no — it does not exist yet** | MS designed it and has not built it; when it exists, MS owns it |
| 7 | `map/mirror/` — pointer or copy | **dropped** | Migration removes the thing it would point at → [MIGRATION.md](MIGRATION.md) |

> **Decision 5 has physical evidence.** A BD entry filename reads
> `handbook__c_d-24-re-는-f-3-pi-mu-d-v-와-정확히-같은-것이다-실행-확인.json` —
> a slug generator passed Korean straight through. Names like that split under
> NFC/NFD normalization, so on a mixed macOS/Windows setup ([PLAN.md](PLAN.md)
> §1.6) the same file looks like two. **Prose in any language; paths in ASCII.**

---

## 7. The seven categories, mapped

| # | Category | Location | Change |
|---|---|---|---|
| 1 | materials | `kb/01-materials/` | unchanged |
| 2 | microscope hardware | `kb/02-hardware/` | unchanged |
| 3 | microscope software | `kb/03-control/` | **narrowed** — the control stack only. Agent code → 4; analysis code → v2 |
| 4 | (sub)agent structure | `map/04-agents/` | **moved zone** — derived, not canonical |
| 5 | physical phenomena | `kb/05-physics/` | **boundary rule added** — the engine-swap test |
| 6 | simulation | `kb/06-simulation/` | the other side of the same rule |
| 7 | key literature and books | `kb/07-sources/` | **split three ways** — `papers/` · `books/` · `raw/` (gitignored) |
| — | — | `kb/00-decisions/` | **added** — where MS's 20 `kb/decisions/` land. Chronological, not a subject |
| — | — | `kb/08-retrieval/` | **added** — retrieval feedback; the only canonical knowledge Librarian holds about itself |
| — | — | `store/` | **added** — challenge, digest and crosswalk are not subjects |
| — | — | `export/` | **added** — how the two repos read offline after migration |

Four of the seven are unchanged, three have adjusted boundaries, one changes
zone, and four zones are added for things that are not subjects.
