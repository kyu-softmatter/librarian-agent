# librarian-agent

[![tests](https://github.com/kyu-softmatter/librarian-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/kyu-softmatter/librarian-agent/actions/workflows/tests.yml)
[![licence: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

**A librarian for three research agents: one canonical knowledge store,
retrieval profiled per calling agent, and custody that includes retirement.**

Drafted 2026-09-06 · **v1 — the microscope agent only**

---

## Why this exists

Three agents already run, and each already keeps a knowledge base. **What does
not exist is the exchange between them**, and two failures were already visible
before this repository was created.

**A knowledge base dies in one of two ways** — nobody fills it, or the index
goes stale so the files are all there and search finds nothing. The second had
already begun: `Brownian-Dynamics-Agent`'s `knowledge/source/papers/INDEX.md`
is headed *do not edit by hand*, names a generator that is **not in the
repository**, and states 40 entries where 42 files exist. A tool that cannot
rediscover that by itself is not doing anything, so that is the first thing this
one is tested against.

**And what each agent needs differs by stage.** Asked one question, the
microscope's photo-perturbation lens and its sample-optics lens want different
evidence — different registries, different gates, different captured priors.
Searching once for both is not efficient and it is not what either asked. So
retrieval here is profiled per caller: the same question deliberately returns
different results depending on who asked.

Two more things follow from being the place knowledge lands.

**Custody has to include retirement.** A store that only accumulates goes stale
by definition. Every entry in all three repositories already carries its own
falsifier — the check that would overturn it — and a falsifier is a work order
nobody has run yet. So this repository also holds the mechanism for doubting a
claim, and the *type* of the falsifier decides who runs it: a measurement goes
to the microscope, a run to the simulator, an unchecked condition of validity to
research-topic.

**And it has to say when it is behind.** Every answer carries `index_stale`, and
a stale index refuses under `--strict`. Deferring a scheduled refresh moves the
job to a person; the flag is what keeps a forgotten refresh from being silent.

---

## Relation to the other three

```text
                    +-------------------------------------+
                    |            research-topic           |
                    |  topic selection (J2)               |
                    |  the form of a pass condition (J3)  |
                    +--+-------------------------------+--+
                       |                               ^
        topics, in falsifiable form                    |   results, dead ends,
        rigor-axis definitions                         |   questions
                       v                               |
     +-----------------+--------+       +--------------+-----------+
     | Brownian-Dynamics-Agent  |       |    agentic-microscope    |
     | simulation               | <---> |    experiment            |
     | A1-A10 . deterministic   |       |    8 lenses . G1-G32     |
     | gate . dimensions first  |       |    BLOCKED by default    |
     +------------+-------------+       +-------------+------------+
                  |                                   |
                  |        read-only ingest           |
                  +---------------+-------------------+
                                  v
                    +-------------------------------+
                    |       librarian  (here)       |
                    |  one store . one index        |
                    |  retrieval per caller         |
                    |  retirement . staleness       |
                    +---------------+---------------+
                                    |
                     generated read-only copy back,
                     so a lens that reads with Grep
                     still works offline
```

| | Owns | Does not |
|---|---|---|
| **agentic-microscope** | instrument state, calibrations, what this setup can physically do | — |
| **Brownian-Dynamics-Agent** | run provenance, seeds, engine versions, non-dimensionalization | — |
| **research-topic** | the form of a pass condition, the canonical-source list, topic candidates | set values or run anything |
| **librarian** *(here)* | the store, the index, retrieval, custody and retirement | **originate numbers · set thresholds · run a simulation or an experiment · settle a challenge whose falsifier it cannot run · decide a topic's value** |

**The prohibitions are inherited, not chosen.** They come from the six
philosophy items and the boundary table in `research-topic`, which were
themselves derived from where the microscope and the simulator independently
converged — so they are not one repository's to change alone.
→ [PLAN.md](PLAN.md) §2

**And this repository is inside the loop, not beside it.** It asks no question
and produces no result, so it is tempting to place it outside the feedback the
other three form. That is wrong: results and dead ends land in its custody and
topic selection reads them from here, so it is on the **return path** — and a
store that decides which evidence surfaces is an amplifier whether or not it
asks anything, because **what a search ranks, it selects.** The tightest form of
that is an agent promoting its own retrieval results to ground truth, which is
why promotion needs human approval and reproduction under two distinct index
states → [FEEDBACK.md](FEEDBACK.md) §5.

Three of those constraints shape everything here:

- **The default is failure.** Zero results is `searched_empty`; an unrecorded
  query is `not_searched`. Neither is "fine".
- **The LLM does not originate numbers.** Every value returned is quoted from a
  file with its location attached — `repo@sha:path#locator` on every hit.
- **Natural language is not state.** Anything used for branching, routing or a
  verdict is an enum, a number, an ID or a boolean. Prose is for humans.

---

## v1 — what is built

Read tools only, over the microscope repository. Measured against
`agentic-microscope` @ `196cdf1`:

| | |
|---|---|
| Documents indexed | **513**, from 59 files, every candidate file accounted for |
| Cross-references | **205** — 144 indexed · 54 present but unindexed · 7 broken |
| Registry coverage rows | **48** |
| Drift findings | **11** |
| Tests | **69** |

```bash
pip install -e ".[dev]"
git clone --depth 1 https://github.com/kyu-softmatter/agentic-microscope.git cache/ms
python -m librarian.cli reindex --repo ms

python -m librarian.cli search "what limits how long I can image this dye" \
    --profile ms:lens-5-photo-perturbation
python -m librarian.cli gaps --missing-only
python -m librarian.cli supplies G10
python -m librarian.cli drift --repo ms
python -m pytest
```

### The six tools

Registered through [`.mcp.json`](.mcp.json) as `python -m mcp_server.server`.
All annotated read-only; nothing writes to any repository.

| Tool | Answers |
|---|---|
| `kb_search` | ranked hits under a named caller profile, each with `repo@sha:path#locator` |
| `kb_get` | one document in full, with both link directions |
| `kb_neighbors` | one hop in the reference graph |
| `kb_supplies` | what supplies a field, or what a gate is waiting for |
| `kb_gaps` | which gate is `BLOCKED`, for want of which input |
| `kb_stale` | whether the index is behind, and whether what is declared still matches what exists |

**Retrieval is profiled, and the profile is a versioned file rather than a query
the model composes.** v1 ships a pair — `ms:lens-5-photo-perturbation` and
`ms:lens-4-sample-optics` — because one profile cannot demonstrate that profiles
do anything. Asked *"what limits how long I can image this dye"*, their top
three are **disjoint**: lens 5 lands in `kb/literature/`, lens 4 in
`kb/expertise/`.

### What it found

None of these was read off a sentence that says so.

- **`G2`, `G3` and `G4` are declared and not implemented.** Each carries a
  threshold and `BLOCKED` as its default in `docs/04-decision-engine.md`, and
  appears in no Python file. They are the optics spectral gates, and
  `optics/checks.py` states its checks as questions with no gate id, so nothing
  ties the implementation to the declaration.
- **`bleach_photons` is absent for all 17 dyes** and `power_at_sample_mw` is
  empty for all 6 sources, so G10 has nothing to count against.
- **The exemplar challenge entry cannot be challenged.**
  `kb/expertise/oil-objective-trapping-in-water.md` is the entry research-topic
  holds up as *"a challenge that was upheld"*, and it carries no falsification
  section where five of the six entries beside it do. By the schema's own rule an
  entry with no falsifier cannot be challenged, so the model case is exempt from
  the rule it models.
- **Seven wikilinks point at entries nobody wrote.**
- **BD's `INDEX.md` defects, rediscovered by tool** — the missing generator and
  40 against 42. That was v1's exit condition.

---

## What comes next

### v1, remaining

| | Blocked on |
|---|---|
| `kb_challenge_raise` — raise a doubt, routed by falsifier type | nothing; next |
| `kb_feedback` — the retrieval-feedback store (`kb/08-retrieval/`) | the publish-gate scope. It stores raw query text and this repository is public: what someone was looking for is what they are about to do → [PLAN.md](PLAN.md) §6.1 |
| The first `kb/literature/` entry | nothing; it is the only KB folder v1 can fill |

### v2 — the simulator, and the acquisition archive

| | Why it waits |
|---|---|
| BD adapters (`wiki` · `source` · `entries` · `runs`) | adapters are additive; bolting one on reshapes nothing |
| **The literature crosswalk** — BD's 42 distillations into the microscope's empty `kb/literature/` | the sharpest gap in the system, and the mapping is already **1→N**: BD files one paper per file with a `provides:` array, the microscope files one quantity per subject, and that array is the decomposition key |
| `envelope.sqlite` — the quantitative index of 2,343 acquisitions | the records live in `D:\data`, outside every repository → **the two things below** |
| Turning "query both" into one query | BD calls its two unmerged knowledge schemas *"the largest piece of debt in the repository"*; indexing both is the read-side fix without merging either |

### v3 — research-topic

The `challenge/` entry kind across all three repositories, and the literature
route's weak resolver: this repository may settle only whether a cited locator
exists and states the condition, and returns `unknown` otherwise. That is
checkable, and it answers a weaker question than the challenge asked.

### Migration, when the tools are trusted

The three knowledge bases move here and are then deleted from their
repositories. **Deletion is the last of five steps and is gated on an
equivalence proof** — the simulator's full test suite identical, the microscope's
G1–G32 verdicts character-identical on a fixed input set, and zero dangling
references. Nothing in either repository reads its KB at runtime, which was
checked rather than assumed; what breaks is the *audit trail* and the lenses that
read with `Grep`, and both fail **silently**. → [MIGRATION.md](MIGRATION.md)

### Not planned

Weekly consolidation is deferred by decision; `index_stale` self-reporting
replaces it, since the refresh itself cannot be deferred. Topic selection and
the definitions of rigor stay with `research-topic` — doing either here would
violate this repository's own prohibitions.

---

## Two things to do at the lab PC

**Both are prerequisites for the acquisition archive.** The tooling is built; what
is open is running it against real files.
The archive is 2,343 acquisitions under `D:\data`, outside every repository.

### 1. Get Librarian running there

```bat
git clone --depth 1 https://github.com/kyu-softmatter/agentic-microscope.git cache/ms
pip install -e .
python -m librarian.cli reindex --repo ms
```

**Then change `.mcp.json`'s `"command"` from `python3` to `python`.** `python3`
is not normally on `PATH` on Windows, and the lab machine is the one that has
the archive. Nothing else is platform-specific: paths in the index are posix and
SQLite is the only native dependency.

### 2. Run the dump — sample one file first

**Built.** `librarian/archive.py`, and two commands.

```bat
librarian archive-sample "D:\data\<one folder>\metadata.txt" --out sample.txt
```

**Do this one first, and read it.** No real Micro-Manager file was available
while the extractor was written, so the `Summary` block's device-tier key names
and nesting are unverified. A sweep run first applies a guessed parser 2,343
times; a sample turns the guess into a diff. It prints what it found — the
Summary key set, whether the first `FrameKey` was reached, the fingerprint, the
camera label, the parsed folder name — and writes the three fragments verbatim
for reading.

```bat
librarian archive-dump "D:\data" --out archive-dump.jsonl --limit 20
librarian archive-dump "D:\data" --out archive-dump.jsonl
```

One JSON object per line, sorted by path, so a repeated sweep produces the same
file. Then bring `archive-dump.jsonl` back; nothing else has to leave the lab PC.

**What it reads** — the three fragments `docs/02-knowledge-base.md` §7 fixes:
`Summary`, the first `FrameKey`, and a 96 kB tail. A file at or under 96 kB is
read whole because the head stops at the first `FrameKey`, and leaving the tail
empty there loses the last timestamp and with it the drop screen.

**What it fills, and what it admits it cannot.**

| Verified | Provisional | Unresolved |
|---|---|---|
| `interval_ms` · `frames` · `width` · `height` · `bit_depth` — the microscope's own regexes, written against real files | the system fingerprint (the key set, not yet the device-label set plus camera serial hash the spec asks for) | the whole device tier — 20 fields `docs/02` §6 declares |
| the drop screen: mean delivered interval against the requested one | the camera label, with `Pirme95B` folded into `Prime95B` | |
| the folder-name rules: `Las10` = level, `Las488` = wavelength, `Las555_5` = 555 nm at 5 % | | |

**Every row carries `unresolved`** — the list of fields looked for and not found
— and the whole `Summary` verbatim in `raw_summary`, so nothing is lost while the
device tier is still a guess. The dump's header records which commit of the
microscope's parser was used.

**A file that yields nothing is recorded, not skipped.** MM 2.0's NDTiff format
carries no `metadata.txt` at all, so such a dataset scans as zero frames, and a
silently absent row is indistinguishable from a clean acquisition. `docs/02` §6
has a `parse_error` column for exactly this.

> **The parser is imported from `cache/ms`, not copied.** The microscope's
> `compute/mm_metadata.py` already tolerates what the files do — MM 1.4 quotes
> its numbers, neither generation guarantees pretty-printing — and a vendored
> copy that drifts from the one it maintains is worse than none, because the
> drift is silent. It is loaded by file path rather than by putting the checkout
> on `sys.path`: the microscope has its own `mcp_server/` package, and
> prepending its root shadows this repository's.

**Still v2:** turning the dump into `kb/envelope.sqlite`. That schema is the
microscope's design and needs the device tier the sample will settle.

---

## Continuous integration

Two jobs, split on what a red build means.

| Job | Runs | Red means |
|---|---|---|
| **unit** | no repository clones, on every push | this repository is internally inconsistent — the badge |
| **integration** | clones the three live remotes | **a source repository moved.** Which is information, not a defect here, so it does not fail the build |

The split is deliberate. The integration tests assert facts about the microscope
at the commit they were written against — that `G2` is still unimplemented, that
seven wikilinks still dangle. When one stops holding, someone should look; it
should not block a change to this repository. The simulator's own CI draws the
same line.

---

## Documents

| Document | Contents |
|---|---|
| [PLAN.md](PLAN.md) | Scope, verified facts, architecture, the tool surface, failure modes, decisions |
| [TREE.md](TREE.md) | The file tree — the top level splits by write authority, not subject |
| [BUILD.md](BUILD.md) | What has to pass before any data is migrated |
| [MIGRATION.md](MIGRATION.md) | How the three knowledge bases move here, and in what order |
| [FEEDBACK.md](FEEDBACK.md) | The retrieval-feedback store, and why "a good answer" cannot be state |

## Licence

MIT — [LICENSE](LICENSE).
