# Migration — moving the three agents' knowledge bases here, then deleting them

Drafted 2026-09-06 · status `draft` · supplements [TREE.md](TREE.md) §3

**Decision: once Librarian is built, the three agents' knowledge bases are
deleted.** This document turns that into an executable order.

**v1 covers MS `kb/` — 40 files. BD's 224 and RT come in v2 and v3**
([PLAN.md](PLAN.md) §0). Taking one repository at a time makes §4 Step 4's
equivalence proof a per-repository proof, which is safer.

It begins with what was actually **checked** to break, because an order guessed at
is an order that is wrong.

---

## 1. What was checked — safer than expected

Verified 2026-09-06 by grep over the code, tests and agent definitions of both
repositories. **Deletion breaks no running code in either.**

| Question | Answer |
|---|---|
| Do MS gates read `kb/` at runtime? | **No.** They read `data/*.yaml` (`optics/components.py` → `fluorophores.yaml` · `filters.yaml` · `pixel_size.yaml`) |
| Do MS tests read `kb/` files? | **No.** Comment citations only |
| Does the BD pipeline read `knowledge/`? | **No.** Only `tools/kb.py`, a CLI tool, reads `knowledge/entries/` |
| Does BD `pytest` read `wiki/benchmarks/`? | **No.** The `benchmark` marker appears in 10+ places, all inside `test_s*.py`, with the values **hardcoded** |
| `tests/test_knowledge.py` | **Does not exist**, though `conftest.py`'s header registers the marker for *"knowledge/wiki/benchmarks regression"* |

**So the KB is already not load-bearing for execution.** That favours the deletion
plan, and it removes the first objection raised against it — that tests would
break. They do not.

### The real consumers are agents and humans, not code

| Consumer | How it reads | After deletion |
|---|---|---|
| MS's 5 lenses | `tools: Read, Grep, Glob` — **no MCP tool declared** | **Cannot read at all** ← decisive |
| BD skill `bd-knowledge` | 10 hardcoded paths in `SKILL.md` (`ls knowledge/wiki/systems/`, `grep -rl … knowledge/source/papers/`) | Commands return empty |
| BD `tools/kb.py` | `ENTRY_DIR = ROOT/"knowledge"/"entries"` | Silently 0 |
| ~27 code comments | `bdbot/constants.py` → `knowledge/wiki/concepts/water-298k.md`; `hardware/lunf_power.py` → `kb/decisions/2026-08-29-…` | **A dangling audit trail** |
| Humans | by opening the repository | Cannot read |

---

## 2. The real risk — it fails silently

**Not one row above raises an error.** `grep` against a missing directory returns
empty, and that is indistinguishable from "there is no knowledge."

**This failure has already happened once and is on record.** BD `tools/kb.py`,
line 42:

> *"This pointed at `kb/entries`, which the merge renamed to `knowledge/entries`.
> The result was not an error — `kb.py list` simply reported 'run-less knowledge 0'
> for 126 existing entries. **A silently empty read is the same failure mode as an
> unwired checker.**"*

And deleting `knowledge/wiki/benchmarks/` takes exactly that shape:

> **The tests keep passing. Only the grounds for their numbers disappear.**
>
> The `@pytest.mark.benchmark` values in `test_s4_nondim.py` and
> `test_s5_scheme.py` are hardcoded, and their justification lives in
> `wiki/benchmarks/`. Delete the grounds and the tests stay green while becoming
> **numbers without a source** — the state BD `docs/03` §4 calls out as *"a number
> without a source is not a number."*

**→ The first task of migration is not moving files. It is updating references.**

---

## 3. `export/` — why a copy goes back

The decisive row in §1: **MS's five lenses declare `tools: Read, Grep, Glob`.**
With no MCP tool they cannot call Librarian. There are two options.

| Option | What it means | Cost |
|---|---|---|
| **(a) Rewrite the agent definitions** | Add MCP tools to 5 lenses and 9 BD agents | Knowledge availability becomes dependent on **a running service**. If MCP is down, a lens returns a verdict with zero knowledge |
| **(b) A generated copy sent back** ★ | Librarian writes a read-only copy into each repo | One more copy |

**(b) is chosen**, because it matches two principles the repos already established.

1. **A derived artefact may be duplicated.** With one canonical copy, the other is
   an index. `export/` has a generator and is regenerated in full, so it satisfies
   [TREE.md](TREE.md) §3's derived-zone invariant.
2. **The default is failure** (constraint ①). A design where knowledge silently
   becomes zero offline uses that principle backwards — it does not fail when it
   should fail, it **looks like it passed when it failed.**

```
Librarian/kb/          ★ canonical. Edited only here
      │
      └─ generate ─▶ Librarian/export/ms/  ─git subtree─▶ MS/kb-export/   ◆ read-only
                     Librarian/export/bd/                 BD/knowledge-export/
```

**Every file in `export/` carries a header with its generator path and Librarian's
commit SHA.** `INDEX.md` surviving without its generator, two entries behind, is
the counter-example that makes this rule necessary.

> This keeps the deletion decision intact — **the canonical copy moves, and what
> remains in the two repos is a derived artefact nobody may hand-edit.**
> "Delete the KB" becomes precisely "delete the KB along with the authority to
> edit it."

---

## 4. The order — deletion is last

> **Step 0 (build + fixture verification) precedes Step 1** → [BUILD.md](BUILD.md).
> Step 1 does not begin until Step 0's acceptance criteria A–E pass.

Each step carries a verifiable exit condition. Deletion is recoverable — it stays
in git history — but **a dangling reference is silent**, so the order is the
safeguard.

### Step 1 · Absorb (both sides alive)

| Task | Exit condition |
|---|---|
| Move content into `kb/` per the §5 table | Source file count = landed file count. Zero loss |
| **Absorb the frontmatter contract** | BD `knowledge/wiki/CLAUDE.md`'s machine contract (`source_frontmatter_required` · `precedence` · `promotion`) is inherited into Librarian `kb/README.md` |
| Build the index | The same query returns the same results from either side |

> **`wiki/CLAUDE.md` is a contract, not a file.** Delete it outright and BD's
> `type` / `author` / `drafted` / `reproduced` vocabulary and its L0–L3 precedence
> rule go with it. `tests/test_s5_pair.py:113` enforces *"do not cite a
> `reproduced: no` literature value as grounds (knowledge/wiki/CLAUDE.md)"* — so
> **without moving the contract first, the grounds for a test disappear before the
> test does.**

### Step 2 · Update references (this is the actual work)

| Task | Exit condition |
|---|---|
| Repoint ~27 code comments | `grep -rn "knowledge/\|kb/"` yields **zero** paths that do not exist |
| BD `bd-knowledge` `SKILL.md`, 10 commands | Replaced with MCP calls or `export/` paths |
| `tools/kb.py` `ENTRY_DIR` | Points at Librarian, or the tool is retired |
| **Add a broken-reference check to CI** | A comment citing a nonexistent path **fails the build** |

> **The last row is the only defence against §2.** It makes the silent failure
> loud. Without it, someone discovers the breakage months later while tracing a
> number back.

### Step 3 · Wire `export/`

| Task | Exit condition |
|---|---|
| The `export/{ms,bd}/` generator | Delete it all, regenerate, **byte-identical** |
| Subtree wiring into both repos | MS's five lenses **find** the migrated knowledge with `Grep` |
| Header rule | Every generated file carries its generator path and Librarian's SHA |

### Step 4 · Prove equivalence

**The gate immediately before deletion.** The only check that decides whether
deletion is allowed.

| Check | Pass condition |
|---|---|
| BD `pytest`, full suite | Identical to the Step 0 baseline |
| MS gate verdicts | For a fixed input set, G1–G32 verdicts are **character-identical** |
| Lens reproduction | On the same question, the five lenses cite the same evidence files as before |
| Dangling references | Zero |

### Step 5 · Delete

One commit, **citing the Step 4 proof in the commit message**. `runs/` is not
deleted (§5).

---

## 5. Where each item lands

Measured file counts. **`runs/` and `research-topic` are not migrated.**

### MS `kb/` — 40 files (v1)

| Source | Count | Destination |
|---|---|---|
| `decisions/` | 20 | `kb/00-decisions/` — chronological, not a subject |
| `systems/` | 8 | `kb/02-hardware/cards/`. But `PyTool_*.reference` and `aresis-support-email-draft.md` go to `03-control` or are classed as not knowledge |
| `expertise/` | 6 | `kb/01-materials/` (coverslip · immersion media · medium RI) · `kb/02-hardware/` (oil-objective trapping) |
| `calibrations/` | 4 | `kb/02-hardware/evidence/measured/`. `disk-bandwidth.yaml` → `03-control` |
| `literature/` | 2 | The rules absorb into `kb/07-sources/`; `_template.md` becomes the form for `kb/0X/evidence/assumed/` |

### BD `knowledge/` — 224 files (v2)

| Source | Count | Destination |
|---|---|---|
| `source/papers/*.md` | 42 | `kb/07-sources/papers/` |
| `source/papers/INDEX.md` | 1 | `map/` — a generated artefact, rewritten **with its generator** |
| `source/books/*.md` | 2 | `kb/07-sources/books/` (distillation only; the original stays out) |
| `wiki/systems/` | 11 | `kb/06-simulation/cards/` — the (system × purpose dynamics) convention unchanged |
| `wiki/concepts/` | 3 | `kb/05-physics/` |
| `wiki/techniques/` | 2 | `kb/06-simulation/` (a HOW-TO is bound to the engine) |
| `wiki/benchmarks/` | 5 | `kb/05-physics/evidence/assumed/` **and `export/bd/`** (they are test grounds — §2) |
| `wiki/findings/` | 23 | `kb/05-physics/findings/` · `kb/06-simulation/findings/`, split by the engine-swap test |
| `wiki/questions/` | 2 | `kb/0X/questions/` |
| `wiki/CLAUDE.md` | 1 | **Contract absorbed** into `kb/README.md`. Not a file move |
| `entries/*.json` | 135 | By `origin`: `tooling` 52 · `method` 45 → `map/04-agents` or `06-simulation` · `handbook` 25 → derived from `07-sources/books` · `intake` 10 → `06-simulation` · `paper` 3 → `07-sources` |
| `runs/*/record.json` | 227 | **Not migrated.** Run provenance is BD's — the index only. There are **256** run directories; 29 hold no post-mortem |

### `research-topic`

**Not migrated.** It keeps topic selection and the definitions of rigor. Of the
seven entry kinds
in `design/kb-schema.md`, Librarian implements only `challenge/` as
`store/challenge/`; the rest remain RT's.

---

## 6. One consequence worth stating — the disclosure direction

BD's 42 `source/papers/` distillations are **public by intent.** BD
`wiki/CLAUDE.md` gives the reason (translated):

> *"Why split by publication status rather than by author — because the disclosure
> boundary applies at **folder** granularity. … What has to be protected is not
> the author but **the fact that it is not yet published.**"*

Three options were open, and **this repository is public by decision (2026-09-06).**

| Option | Result |
|---|---|
| (a) Publish `kb/07-sources/` only | Inherits BD's original rule |
| **(b) Librarian fully public** | ✅ **Decided.** The "recall of public assets" problem disappears. The price: a weekly digest could expose unpublished research directions (`T-019`①) |
| (c) Librarian fully private | Recalls 42 public assets |

**With (b), §6's original worry is resolved** — the 42 distillations stay public
after migration. **What remains is the burden in the other direction:** a rule for
what may be *written* here, which is the `publish-gate`. The first path that opens
is not the digest (deferred) but `kb/08-retrieval/sessions/`, which stores query
text → [PLAN.md](PLAN.md) §6.1. Same layer of rule as `kb/07-sources/raw/` being
gitignored.

---

## 7. Decisions

| # | Decision | Value | Grounds |
|---|---|---|---|
| 1 | Offline read path | **`export/` generated copies** | §3(b). Otherwise a lens returns a verdict with zero knowledge when MCP is down |
| 2 | Visibility | ✅ **fully public — 2026-09-06** | The `publish-gate` becomes a precondition for the digest |
| 3 | `tools/kb.py` | **retired** (Librarian MCP replaces it) | Its `ENTRY_DIR` returns 0 silently |
| 4 | Broken-reference CI check | **required at Step 2** | §2's silent failure otherwise stays |
| 5 | `runs/` (227 records in 256 directories) | **not migrated**; indexed only | Otherwise ownership of run provenance blurs |
| 6 | `entries/` (135) decomposition | by `origin` (§5) | Otherwise 52 + 45 tooling/method entries pollute the subject folders |
| 7 | Migration order | **MS first**, then BD, then RT | Step 4's proof becomes per-repository |
| 8 | Deletion timing | after Step 4 passes | — |
