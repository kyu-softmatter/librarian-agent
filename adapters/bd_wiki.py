"""BD `knowledge/wiki/` -- the synthesis layer, six declared types.

The contract (`wiki/CLAUDE.md`) fixes what a page must carry —
`wiki_frontmatter_required: [type, author, drafted]` — and what the types are.
This adapter reads that file for the vocabulary; see `_bd.contract`.

  concepts/     WHAT-IS   -> card
  techniques/   HOW-TO    -> card
  systems/      the (system x purpose-dynamics) card, where the
                nondimensionalisation convention is fixed        -> card
  benchmarks/   validation oracles, plus `benchmarks.yaml`       -> assumed
  findings/     Q -> A with citations, `dead-end-*` included     -> finding
  questions/    open, closed by status rather than deletion      -> question

**`benchmarks.yaml` is indexed as rows, not as a file.** It is the ledger
`pytest` reads, and it holds more benchmarks than the folder holds pages -- 7
running against 5 `.md` files, plus 2 ordinal and 5 blocked. A file-level
document would make the ledger findable and its individual expected values not,
which is the half that a caller asking *"what is the expected value here"*
needs.

**Korean headings are the normal case here, and locators stay ASCII.**
`librarian.md.slug` collapses a non-ASCII heading to a digest for exactly this
corpus: BD's own `entries/` filenames already broke under NFC/NFD across macOS
and Windows, and a locator is a coordinate rather than prose.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from librarian.doc import Doc
from librarian.md import first_heading, frontmatter, has_falsifier, sections

from ._bd import contract, kind_for, reproduced, value

#: The ledger lists benchmarks under three headings, and all three are worth
#: indexing. `blocked` is the list of physics the engine cannot reproduce yet,
#: and the ledger's own comment calls that list an asset -- it is the same
#: statement `kb_gaps` makes about a BLOCKED gate, written by hand.
_LEDGER_SECTIONS = ("benchmarks", "ordinal", "blocked")


def _md(path: Path, rel: str, sha: str, root: Path) -> list[Doc]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = frontmatter(text)

    declared = value(fm.get("type"))
    kind = kind_for(root, declared)
    # A benchmark page states a value taken from the literature or an analytic
    # limit, which is `assumed` by MS's tier rule and never advances a verdict.
    evidence = "assumed" if kind == "assumed" else None

    # `question` is the title a reader scans for where the page states one --
    # BD's findings carry the question they answer, the same shape as MS's
    # expertise entries.
    title = (value(fm.get("question"))
             or first_heading(body, level=1)
             or value(fm.get("system"))
             or path.stem)

    common = dict(
        repo="bd", path=rel, commit_sha=sha, kind=kind,
        origin=declared,
        evidence=evidence,
        tier=3 if evidence == "assumed" else None,
        reproduced=reproduced(fm.get("reproduced")),
        has_falsifier=has_falsifier(text),
        # `status` is the page's own lifecycle (draft | usable | validated for a
        # card, open | answered for a question). It conditions the claim, so it
        # travels with it rather than being dropped.
        conditions=value(fm.get("status")),
    )

    out = [Doc(locator=s.locator,
               title=f"{title} -- {s.title}" if s.title else title,
               body=s.body, **common)
           for s in sections(body)]
    if not out:
        out.append(Doc(locator="#", title=title, body="", **common))
    return out


def _ledger(path: Path, rel: str, sha: str) -> list[Doc]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace"))
    except yaml.YAMLError as e:
        raise ValueError(f"{rel}: {e}") from e
    if not isinstance(data, dict):
        return []

    out: list[Doc] = []
    for section in _LEDGER_SECTIONS:
        rows = data.get(section)
        if not isinstance(rows, list):
            continue
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            ident = value(row.get("id")) or str(i)
            out.append(Doc(
                repo="bd", path=rel, locator=f"{section}.{ident}", commit_sha=sha,
                kind="assumed", origin=section,
                # Layer 2 of BD's four evidence layers is an analytic limit and
                # layer 3 a literature benchmark. Neither is a measurement made
                # here, so neither advances a verdict.
                evidence="assumed", tier=3,
                title=f"{section} {ident}"
                      + (f" -- {value(row.get('observable'))}"
                         if row.get("observable") else ""),
                body=yaml.safe_dump(row, allow_unicode=True, sort_keys=True),
                conditions=value(row.get("source")),
            ))
    return out


def bd_wiki(root: Path, sha: str) -> list[Doc]:
    wiki = root / "knowledge" / "wiki"
    if not wiki.is_dir():
        raise FileNotFoundError(f"{wiki} does not exist")
    contract(root)                      # absent or unparseable is a hard failure

    out: list[Doc] = []
    for path in sorted(wiki.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix == ".md":
            out.extend(_md(path, rel, sha, root))
        elif path.name == "benchmarks.yaml":
            out.extend(_ledger(path, rel, sha))
    return out
