# `kb/` — the canonical store

**Everything here is canonical. Nothing here is regenerable.**
That is the whole reason the top level splits by write authority rather than by
subject ([../TREE.md](../TREE.md) §3).

| Zone | May be deleted and rebuilt |
|---|---|
| `kb/` | **no** |
| `map/` · `index/` · `export/` | yes — the rebuild is canonical |
| `store/` | no (it is a record) |
| `cache/` | yes |

## Why number 04 is missing

The seven categories this store was asked for included *the structure and
function of each (sub)agent*. That one is **derived** — a commit to any source
repository makes it stale — so it lives at `map/04-agents/` and is regenerated in
full, never hand-edited.

**The gap in the numbering is the marker for that rule.** A folder that a human
may edit and a folder a generator overwrites cannot sit on the same level: the
refresh either erases what a human wrote, or it stops running and the derived
half rots. BD's `knowledge/source/papers/INDEX.md` is the observed case — headed
*do not edit by hand*, naming a generator that is no longer in the repository,
and two entries behind.

## The one rule

> **Prose goes only in fields a human reads. Any field used for branching,
> routing or a verdict must be a formal value.**

The local form of BD `I-133`. The check, per field: **what code reads this and
branches on it?** If anything branches, it must be an enum, a number, an ID or a
boolean. If only a human reads it, prose is fine.

| Role of the field | Allowed |
|---|---|
| state · verdict · routing key | enums only |
| identifier · reference | an ID (a string, but **not free text**) |
| the **location** of evidence | ID + coordinates (DOI, section, table row) |
| the **content** of evidence | prose |
| a value claim | **no scalar score** |

## Frontmatter contract

Machine-read. **Code parses this, and does not hard-code paths** — BD
`wiki/CLAUDE.md` states that instruction directly, and hard-coding is what
produced the orphaned `INDEX.md`.

```yaml
id: <filename without extension>
kind: card | measured | assumed | finding | question | decision | source
evidence: measured | assumed | confirmed_default     # branchable
tier: <integer>                                       # branchable
provenance: from_paper | from_knowledge | assumed | derived | from_drawing
source: "<locator into a source, or a path into a source repo>"
scope: "<where this applies, and where it stops>"
review_after: <YYYY-MM-DD>
supersedes: null
superseded_by: null
author: agent | human | hybrid
drafted: <YYYY-MM-DD>
```

`evidence` decides whether a verdict may advance, and **only `measured` may.**
A literature value is always `assumed`, so it lets a gate compute instead of
refusing, and never claims anyone measured the quantity here.

**Every entry carries the check that would overturn it.** An entry with no
falsifier cannot be challenged, and that is a defect in the entry rather than a
gap in the mechanism — the index reports the `has_falsifier = 0` list as exactly
that.

> **To be absorbed at MIGRATION Step 1:** BD `knowledge/wiki/CLAUDE.md`'s full
> machine contract — `source_frontmatter_required`, `precedence` L0-L3,
> `promotion: finding_to_concept: human_gated`, and the `reproduced` vocabulary
> that `tests/test_s5_pair.py:113` enforces. **Moving the contract precedes moving
> the files**, or the grounds for a test disappear before the test does.

## Naming

**Paths are ASCII. Prose is any language.** A BD entry filename reads
`handbook__c_d-24-re-...-것이다-실행-확인.json`, produced by a slug generator that
passed Korean straight through. Names like that split under NFC/NFD normalization,
so on a mixed macOS/Windows setup the same file looks like two.

## Folders

| Folder | v1 | Shape |
|---|---|---|
| [`00-decisions/`](00-decisions/) | ✅ | one dated decision per file |
| [`01-materials/`](01-materials/) | ✅ | five slots |
| [`02-hardware/`](02-hardware/) | ✅ | five slots |
| [`03-control/`](03-control/) | ✅ | five slots |
| `04` | — | **absent by design** -> `map/04-agents/` |
| [`05-physics/`](05-physics/) | v2 | five slots |
| [`06-simulation/`](06-simulation/) | v2 | five slots |
| [`07-sources/`](07-sources/) | ✅ | `papers/` `books/` `raw/` |
| [`08-retrieval/`](08-retrieval/) | ✅ | `sessions/` `oracles/` `findings/` |
