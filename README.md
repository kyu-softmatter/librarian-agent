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

## The four, and what flows on each edge

```text
                     +-------------------------------------+
                     |            research-topic           |
   +--------2------->|  topic selection (J2)               |
   |                 |  the form of a pass condition (J3)  |
   |                 +--+-------------------------------+--+
   |                    | 1                           1 |
   |                    v                               |
   |  +-----------------+--------+       +--------------+-----------+
   |  | Brownian-Dynamics-Agent  |       |    agentic-microscope    |
   |  | simulation               |<--1-->|    experiment            |
   |  | 9 agents . A1-A10        |       |    8 lenses . G1-G32     |
   |  | dimensions first         |       |    BLOCKED by default    |
   |  +--------+---------+-------+       +-------+---------+--------+
   |         3 |       4 ^                     3 |       4 ^
   |           v         |                       v         |
   |  +--------+---------+-----------------------+---------+--------+
   |  |                     librarian   (here)                      |
   |  |      a server over a store, not a conversational agent      |
   |  |                                                             |
   |  |   kb/        the one canonical store                        |
   |  |   index/     FTS5 . every hit carries repo@sha:path#locator |
   |  |   map/       04-agents/ . ms . bd . rt . lib -- all four    |
   |  |   profiles/  one per caller, versioned, applied server-side |
   +--+   store/     challenge . digest . inbox                     |
      +--------+---------------------------------------+------------+
             5 |                                     6 |
               v                                       v
      +--------+-----------------------+   +-----------+------------+
      | who may ask, under a profile   |   | ms/kb-export           |
      | ms:lens-*  bd:s*  rt:V*        |   | bd/knowledge-export    |
      | human:* -- role and purpose    |   | read with Grep,        |
      |                                |   | offline, no MCP tool   |
      | stdio . one machine: scope PC  |   | declared               |
      +--------------------------------+   +------------------------+
```

**Three of the four boxes are conversational agents. The fourth is not** — it has
no session and no context window, which is why it can hold the store at all
→ [PLAN.md](PLAN.md) §3.3.

| # | Edge | What travels | Exists |
|---|---|---|---|
| **1** | among the three agents | topics in falsifiable form and rigor-axis definitions outward; results, dead ends and open questions back | today |
| **2** | librarian → research-topic | **the return path.** Results land in custody and topic selection reads them from here — which is why this repository is *inside* the loop rather than beside it | v3 |
| **3** | agent → librarian | read-only ingest over `git fetch`. The commit sha becomes every hit's provenance, and no source repository is ever written | **ms v1** · bd v2 · rt v3 |
| **4** | librarian → agent | a challenge, routed by its falsifier's **type** and never by the sender: a measurement to ms, a run to bd, a condition of validity to rt, and none available to a person | **v1** — `kb_challenge_raise` |
| **5** | librarian → caller | an answer — hits carrying `repo@sha:path#locator`, an evidence tier and `index_stale`, and never a number of its own | **v1** |
| **6** | librarian → repository | `export/`, a generated read-only copy, so a lens that declares only `Read, Grep, Glob` keeps working offline | MIGRATION Step 3 |

**Edge 4 is the only one that runs against the direction of ingest,** and it is
what makes custody include retirement rather than accumulation: a falsifier is a
work order nobody has run yet, and the librarian hands it to whoever can run it
instead of settling it itself. Research-topic's own two edges (3 and 4) are left
out of the picture rather than out of the design — they arrive in v3, and drawing
them now would cost the legibility of the three that exist.

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

**And it is inside the loop, not beside it.** It asks no question and produces no
result, so it is tempting to place it outside the feedback the other three form.
**Edge 2 is why that is wrong** — and a store that decides which evidence
surfaces is an amplifier whether or not it asks anything, because **what a search
ranks, it selects.** The tightest form of that is an agent promoting its own
retrieval results to ground truth, which is why promotion needs human approval
and reproduction under two distinct index states
→ [FEEDBACK.md](FEEDBACK.md) §5.

Three of those constraints shape everything here:

- **The default is failure.** Zero results is `searched_empty`; an unrecorded
  query is `not_searched`. Neither is "fine".
- **The LLM does not originate numbers.** Every value returned is quoted from a
  file with its location attached — `repo@sha:path#locator` on every hit.
- **Natural language is not state.** Anything used for branching, routing or a
  verdict is an enum, a number, an ID or a boolean. Prose is for humans.

---

## v1 — what is built

Seven read tools and two writes. Measured 2026-09-15 against
`agentic-microscope` @ `9f971a8`
and `Brownian-Dynamics-Agent` @ `a18e171` — **the command that computes each row
is below the table**, because every figure here has already gone stale once:

| | |
|---|---|
| Documents indexed | **1,446** — 626 from the microscope, 820 from the simulator, every candidate file accounted for |
| Cross-references | **557** — 437 indexed · 91 present but unindexed · 29 broken |
| Registry coverage rows | **25** |
| Drift and defect findings | **34** |
| Tests | **189**, 155 of them offline |

```bash
pip install -e ".[dev]"
git clone --depth 1 https://github.com/kyu-softmatter/agentic-microscope.git cache/ms
git clone --depth 1 https://github.com/kyu-softmatter/Brownian-Dynamics-Agent.git cache/bd

# Both repos in one command. `--repo ms` alone rebuilds in full and drops bd.
python -m librarian.cli reindex --repo ms --repo bd

python -m librarian.cli search "what limits how long I can image this dye" \
    --profile ms:lens-5-photo-perturbation
python -m librarian.cli gaps --missing-only
python -m librarian.cli supplies G20
python -m librarian.cli inputs radial_stiffness_n_per_m
python -m librarian.cli drift --repo ms
python -m pytest
```

### The nine tools

Registered through [`.mcp.json`](.mcp.json) as `python -m mcp_server.server`.
Seven are annotated read-only. **Nothing writes to any source repository,
ever** — a challenge is handed to whoever can run the falsifier, not applied to
their files.

| Tool | Answers |
|---|---|
| `kb_search` | ranked hits under a named caller profile, each with `repo@sha:path#locator` |
| `kb_inputs` | **what a computation needs, and which of it exists** — the closure over a signature |
| `kb_get` | one document in full, with both link directions |
| `kb_neighbors` | one hop in the reference graph |
| `kb_supplies` | what supplies a field, or what a gate is waiting for |
| `kb_gaps` | which gate is `BLOCKED`, for want of which input |
| `kb_stale` | whether the index is behind, and whether what is declared still matches what exists |
| `kb_feedback` | **writes.** Which hits a search was actually answered with — one local, uncommitted session |
| `kb_challenge_raise` | **writes.** Doubt against a claim, routed by the type of the falsifier it cites |

**`kb_feedback` is the only one that writes, and what it records is a fact.**
Not *"the answer was good"* — a judgment, and unstorable — but *"these are the
uids I cited"*, which is also a test: retrieval has no grader, so a past
confirmed citation stands in for one. It is never inferred from what the caller
was sent, because inferred it stops being a fact. There is no satisfaction
score anywhere, deliberately: averaged, twenty ranking failures and twenty
missing entries are the same number, while the fix for one lives in `profiles/`
and for the other in `kb/`.

It also refuses `not_searched`, which is the default of a query nobody
recorded — *this was never checked*, rather than *it was fine*. Calling the
tool is the record that someone looked, so it cannot be the verdict.

**And `kb_challenge_raise` is the edge that runs against ingest.** A challenge
is a work order nobody has run yet, routed by the **type** of the falsifier it
cites and never by who sent it. `falsifier_cited` is mandatory and has to point
into the target's own file: citing a new basis instead turns a work order back
into an argument. An entry carrying no falsifier cannot be challenged at all —
a defect in the entry, since every judgment is supposed to carry the check that
would overturn it, and the fix is a pull request against whoever holds it.

**Promotion to a regression oracle is not a tool.** An agent promoting its own
retrieval results to ground truth is a self-confirming loop — what ranks high
gets cited, having been cited it becomes an oracle, being an oracle keeps it
ranked high — and human approval is the only damping on it. It takes **two**
assertions from a person, because they are judgments about different things:
that the result is an oracle, and that its raw query may enter a public
repository.

```bash
python -m librarian.cli sessions
python -m librarian.cli promote --profile ms:lens-4-sample-optics \
    --approve --publish-query "coverslip thickness for the oil objective"
python -m librarian.cli oracles
```

**An oracle is a past confirmed citation, re-run — and it has to actually catch
a regression.** That is fixture F9, and its pass condition is that something
*fails*: break the profile on purpose and the oracle must go red. Stay green and
it is an unwired checker, which is BD's recorded failure — `tools/kb.py` pointed
at a renamed path and reported *"run-less knowledge 0"* for 126 existing
entries. Checked on a fixture corpus **and** on the real one: lowering
`ms:lens-4-sample-optics`'s `expertise` weight from 1.9 to 0.5 drops the entry
out of the top slot and the oracle notices. F9 was then mutation-tested, because
a fixture whose pass condition is a failure can pass for the wrong reason.

### It is a server, not a fourth agent

Three conversational agents already run, and this is deliberately not a fourth.
An LLM call is **stateless**, so a librarian that reasoned would reload its own
prompt and its own description of the corpus on *every* request — and the corpus
is precisely what has to be remembered between requests. So the store is code
(`kb/` and `index/kb.sqlite`, no model, **zero tokens**) and the librarian is the
tool surface over it. "Retrieval that knows who asked" follows from the same
split: it is a **parameter** — a versioned profile applied server-side — not a
model inferring what the caller probably meant.
→ [PLAN.md](PLAN.md) §3.3

**And "callable whenever an agent needs it" is three claims, not one.**

| | The claim | What breaks it |
|---|---|---|
| 1 | the server is running | stdio dies with the session that spawned it. **No MCP client manages a server's lifetime** — an always-on one is systemd's or docker's job, not a caller's |
| 2 | it was registered at startup | `.mcp.json` is read once, so the set of reachable servers is **closed** for that session |
| 3 | then it can be called freely | each call is independent; whatever has to survive two calls is in the index, or it does not exist |

**It runs on stdio, and everything runs on the microscope PC** — all four
systems, one machine, with separation deferred until the system is understood
well enough to be worth splitting. This replaces an earlier plan for an
always-on service on the lab NAS, and the correction is a subtraction: that
service was never wanted for itself, only forced by a second machine. There
isn't one — the simulator's macOS is a **development** environment, and it
passes CI and runs anywhere.

So one thing remains open where two did. Reads are already safe to run
concurrently: several agents mean several spawned processes, the server opens
the index **read-only and per call**, and a rebuild is picked up on the next
call rather than held stale by a live session. **Concurrent writes are
undefined**, and that is now the only thing that would force a service.
→ [PLAN.md](PLAN.md) §3.4

**People are the second class of caller, and they arrive the same way.** A person
asks in their own words through **their own MCP client**, so the answer is
composed by the model they are already talking to and the librarian still returns
nothing but quoted text with coordinates — no synthesis layer, and no model
inside the server. What it does add is a profile namespace: `human:*` roles plus
a `purpose` argument, keyed by **role, not by person** — profiles should multiply
with kinds of question rather than with people, and a person-keyed one would
record who was looking for what in a public repository. It also turns
`caller_profile` into an identity claim that nothing yet checks — harmless
among trusted agents on one machine, and it becomes load-bearing only on an
endpoint several people reach independently, which is a question that now
arrives with the separation rather than with BD.
→ [PLAN.md](PLAN.md) §3.5

**And the four agents' own definitions are part of the store.**
`map/04-agents/` already carries the microscope's five lenses with the gates each
one owns, read from its `.claude/agents/`; BD's nine agents follow, then
research-topic's two personas, and the fourth slot is **this** repository —
generated from `profiles/` and the tool surface, because it has no `.claude/` of
its own. That is what lets an answer say *which lens declares `G10`*, at a
locator. It is deliberately **not** a way to guess which lens you are: the map
supplies the correspondence and the caller makes the choice, because a guessed
profile changes which evidence comes back and nothing in the answer shows that it
was guessed. → [PLAN.md](PLAN.md) §3.6

### Asking for the inputs to a calculation

An agent's question is usually not *"what do we know about trap stiffness"* —
`kb_search` answers that — but **"give me what I need to compute trap stiffness
on this instrument."** Those are different queries, and the second has an answer
no ranking can reach: it is the closure over a function's signature.

```
kb_inputs("radial_stiffness_n_per_m")            status: blocked

  unresolved  power_w                <- kb/decisions/2026-08-27-tweezers-first-light
                                        -measured-limits.md#6-laser-power-is-not-
                                        reachable-from-software-at-all
  ready       bead.radius_m          <- data/particles.yaml > diameter_um   3/8
                                        [alias: halve it, um -> m]
  unresolved  bead.n                 ?  data/particles.yaml#materials.polystyrene
  unresolved  medium.n               ?  kb/expertise/sample-medium-refractive-index
  ready       beam.na                <- data/objectives.yaml > na           6/6
  unresolved  beam.wavelength_m      ?  data/filters.yaml#filters.OT-Dichroic-750LP
```

Asked for *the objective list, the laser power per setting, and the sample
refractive index*, that is the answer: the objective list is there in full
(6 of 6), the refractive index is a captured prior rather than a registry field
so it arrives as a citation, and **the laser power is the one the instrument
cannot supply** — `power_at_sample_mw` is empty for all six sources including
`Trap`, and the top-ranked document says why: *laser power is not reachable from
software at all.*

**The closure is derived from the signature, not hand-authored.** A written-down
input list is the stale-table problem again — it goes wrong the first time an
argument is added, and nothing notices. Where a name genuinely cannot bridge two
things (`radius_m` against `diameter_um`, different quantity and different
units) the link is recorded in [`profiles/_field-aliases.yaml`](profiles/), is
**verified against the registries on every build**, and a stale one becomes a
finding. Anything left over is `unresolved` with ranked candidates and the query
that found them — because `n` is one character, cannot be a search term, and the
class that declares it can be.

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
| ~~`kb_challenge_raise` — raise a doubt, routed by falsifier type~~ | **Built.** It was waiting on nothing |
| ~~`kb_feedback` — the retrieval-feedback store~~ | **Built.** The publish-gate scope was the blocker and is settled: `sessions/` is local only and permanently, and raw query text is committed only in `oracles/`, where promotion's human approval is also the disclosure review → [PLAN.md](PLAN.md) §6.1 |
| The first `kb/literature/` entry | nothing; it is the only KB folder v1 can fill |

### v2 — the simulator, and the acquisition archive

| | Why it waits |
|---|---|
| BD adapters (`wiki` · `source` · `entries` · `runs`) | adapters are additive; bolting one on reshapes nothing |
| **The literature crosswalk** — BD's 42 distillations into the microscope's empty `kb/literature/` | the sharpest gap in the system, and the mapping is already **1→N**: BD files one paper per file with a `provides:` array, the microscope files one quantity per subject, and that array is the decomposition key |
| `envelope.sqlite` — the quantitative index of 2,343 acquisitions | the records live in `D:\data`, outside every repository → **the two things below** |
| Turning "query both" into one query | BD calls its two unmerged knowledge schemas *"the largest piece of debt in the repository"*; indexing both is the read-side fix without merging either |
| ~~One always-on server on the lab NAS~~ | **Dropped 2026-09-15.** It was forced by a second machine, and there is none — everything runs on the microscope PC. What is left in its place is a **concurrent-write policy**, which is a policy and not a host → [PLAN.md](PLAN.md) §3.4 |
| `human:*` role profiles, and a `purpose` argument | people are the second caller class, and the first whose declared role nothing checks → [PLAN.md](PLAN.md) §3.5 |
| `map/04-agents/lib/` — the fourth agent's own definitions | it is generated from `profiles/` and the tool surface, so it settles once the role profiles above do → [PLAN.md](PLAN.md) §3.6 |

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
