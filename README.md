# librarian-agent

[![licence: MIT](https://img.shields.io/badge/licence-MIT-blue.svg)](LICENSE)

A librarian for the other three agents:
[agentic-microscope](https://github.com/kyu-softmatter/agentic-microscope) (experiment) ·
[Brownian-Dynamics-Agent](https://github.com/kyu-softmatter/Brownian-Dynamics-Agent) (simulation) ·
[research-topic](https://github.com/kyu-softmatter/research-topic) (proposal and validation).

**One canonical knowledge store, retrieval profiled per calling agent, and
custody that includes retirement.** The fourth axis: the other three produce
knowledge and enforce their own domains; this one keeps it findable and reports
when it has gone stale.

> [!IMPORTANT]
> **v1 is the microscope agent only.** Six read tools over an index of that
> repository. No knowledge has been migrated yet — the store is built and empty
> by design, because a form fixed after it is filled throws away what was filled.
> → [PLAN.md](PLAN.md) §0

---

## Two things to do at the lab PC

**These are the prerequisites for the acquisition archive, and both are still
open.** The archive is 2,343 acquisitions under `D:\data`, outside every
repository — the reason `envelope.sqlite` is deferred to v2
([PLAN.md](PLAN.md) §0.3).

### 1. Get Librarian running there

```bat
git clone --depth 1 https://github.com/kyu-softmatter/agentic-microscope.git cache/ms
pip install -e .
python -m librarian.cli reindex --repo ms
```

**Then change `.mcp.json`'s `"command"` from `python3` to `python`.** `python3`
is not normally on `PATH` on Windows, and the lab machine is the one that has
the archive. Everything else is platform-independent: paths in the index are
posix, and the only native dependency is SQLite.

### 2. Decide and build the metadata dump

The dump is what makes the archive ingestible without installing Librarian
permanently on the lab PC, and it keeps the decision reversible
([PLAN.md](PLAN.md) §9 open item b: run there, or ingest an export).

**The scope is already specified and does not need designing** — MS
`docs/02-knowledge-base.md` §7 fixes it:

| Item | What the spec says |
|---|---|
| Size | Up to 44 MB per file. **Stream the header only** — `Summary` + the first `FrameKey` + a 96 kB tail |
| Two schemas | MM 1.4.23 (2,137 acquisitions, 91 %) differs from 2.0.3 |
| System identity | Distinguishing by PC name gets it wrong. Use the device-label set plus a camera chip/serial hash |
| Label typos | `Prime95B` vs `Pirme95B` in 20 acquisitions — an alias table is needed |
| Folder names | `Las10` = level, `Las488` = wavelength, `Las555_5` = 555 nm at 5 %. An integer in 350–800 is a wavelength |
| Cheap drop screen | From the tail's `ElapsedTime-ms`: `(last − first) / (n − 1)` is the mean delivered interval, so it exceeds the requested interval exactly when frames went missing. It cannot say **where** or **how many** — that needs every timestamp |

**So three fragments per file, not 44 MB.** At 2,343 files the dump is still
substantial, which is why it is worth writing the extractor before the session
rather than during it.

**Not built yet.** The extractor and the `envelope.sqlite` schema are v2 work.

---

## What is built

Measured against `agentic-microscope` @ `196cdf1`:

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
All read-only; nothing writes to any repository.

| Tool | Answers |
|---|---|
| `kb_search` | ranked hits under a named caller profile, each with `repo@sha:path#locator` |
| `kb_get` | one document in full, with both link directions |
| `kb_neighbors` | one hop in the reference graph |
| `kb_supplies` | what supplies a field, or what a gate is waiting for |
| `kb_gaps` | which gate is `BLOCKED`, for want of which input |
| `kb_stale` | whether the index is behind, and whether what is declared still matches what exists |

The write half — `kb_challenge_raise` and `kb_feedback` — is not here. A
challenge routes by the type of the falsifier it cites, and a retrieval record
stores raw query text in a repository that is public, so the publish-gate scope
is settled first (→ [PLAN.md](PLAN.md) §6.1).

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
  section where five of the six entries beside it do.
- **Seven wikilinks point at entries nobody wrote.**
- **BD's `INDEX.md` names a generator that is not in the repository** and states
  40 entries where 42 files exist — the two defects that were found by reading,
  rediscovered by tool, which is Phase 0's exit condition.

---

## Documents

| Document | Contents |
|---|---|
| [PLAN.md](PLAN.md) | Scope, verified facts, architecture, the tool surface, failure modes, decisions |
| [TREE.md](TREE.md) | The file tree — the top level splits by write authority, not subject |
| [BUILD.md](BUILD.md) | What has to pass before any data is migrated |
| [MIGRATION.md](MIGRATION.md) | How the three knowledge bases move here, and in what order |
| [FEEDBACK.md](FEEDBACK.md) | The retrieval-feedback store, and why "a good answer" cannot be state |

Constraints are inherited rather than invented: the six philosophy items and the
boundary table in `research-topic` are not this repository's to change alone.

## Licence

MIT — [LICENSE](LICENSE).
