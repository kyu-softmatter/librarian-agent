# `kb/07-sources/` — literature and books

One distillation per source. **The original never enters the repository.**

```
papers/    one distillation per published source, in-git
books/     distillation only
raw/       gitignored — PDFs and originals live in a local cache
```

**Why the original stays out.** BD solved this and the contract carries over: an
`origin: handbook` entry's source reads `distillation#section <- [short-name]
p.page`, so *a claim can be walked back to the page it came from without the book
being in the repository*. `raw/` is a local cache; `source_url` in the
frontmatter is how anyone else fetches it.

**The unit of storage differs from BD's, deliberately.** BD files one paper per
file with a `provides:` array; MS files **one quantity per subject**
(`bleach-photons-alexafluor488.md`, not `smith-2019.md`) because *"the unit of
storage is the number a gate consumes, not the paper it came out of."*

Both are kept: the distillation lives here, and the per-quantity entries it
supplies live in the relevant subject folder under `evidence/assumed/`. BD's
`provides:` array is the decomposition key, so the mapping is **1 to N**
([../../PLAN.md](../../PLAN.md) §1.4).

No `cards/` — a source is not a convention.
