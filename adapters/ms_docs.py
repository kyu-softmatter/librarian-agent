"""MS `docs/*.md` -- section anchors as locators.

The design documents are where MS states its own rules: the 3-tier
normalization, the decision order, the gate table with thresholds, the parser
spec for the acquisition archive. They are indexed at section granularity
because a rule cited without its section is not checkable.

`docs/` is also where the gate table lives that `librarian/drift.py` compares
against the code -- the source of the G2/G3/G4 finding.
"""

from __future__ import annotations

from pathlib import Path

from librarian.doc import Doc
from librarian.md import first_heading, frontmatter, has_falsifier, sections


def ms_docs(root: Path, sha: str) -> list[Doc]:
    docs = root / "docs"
    if not docs.is_dir():
        raise FileNotFoundError(f"{docs} does not exist")

    out: list[Doc] = []
    for path in sorted(docs.rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        _, body = frontmatter(text)
        doc_title = first_heading(body) or path.stem
        falsifier = has_falsifier(text)
        for s in sections(body):
            out.append(Doc(
                repo="ms", path=rel, locator=s.locator, commit_sha=sha,
                kind="doc_section", origin="docs",
                has_falsifier=falsifier,
                title=f"{doc_title} -- {s.title}" if s.title else doc_title,
                body=s.body,
            ))
    return out
