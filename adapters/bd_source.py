"""BD `knowledge/source/` -- one distillation per original, the original absent.

`raw/` is gitignored on purpose: the copyrighted PDF never enters the repository
and the in-git distillation is canonical, with `source_url` in the frontmatter
for anyone who needs the original. So what is indexed here is the distillation,
and a hit points at the section of it that states the thing.

The contract splits the folder **by publication rather than by author**, and
says why: the disclosure boundary is drawn per folder, so filing a lab paper
beside unpublished assets would take an already-DOI'd distillation private along
with them. A lab paper therefore sits in `papers/` and carries
`lab_authored: true` -- which `Doc` has a field for.

**`reproduced` is tracked independently of publication.** The contract is blunt
about it: a parameter from a published lab paper is not grounds until we have
reproduced it, because appearing in a paper does not mean the value works in our
code. PLAN.md 5.1 already decided the retrieval consequence -- `reproduced: no`
is **demoted, never excluded**, since it is still the right pointer.

**`papers/INDEX.md` is indexed and marked, not skipped.** It is a generated file
whose generator is not in the repository -- the decay this project exists to
catch, and `drift.generator_missing` reports it under its own name. Skipping it
here would add a second report of the same fact as `file_produced_nothing`;
indexing it with `origin: generated` lets a profile demote it and keeps the
coverage check honest about what was read.
"""

from __future__ import annotations

from pathlib import Path

from librarian.doc import Doc
from librarian.md import first_heading, frontmatter, has_falsifier, sections

from ._bd import reproduced, value

#: The one file in `source/` that is derived rather than distilled.
_GENERATED = {"INDEX.md"}


def _doc_set(path: Path, rel: str, sha: str) -> list[Doc]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = frontmatter(text)

    generated = path.name in _GENERATED
    # `kind` in BD's vocabulary is the source kind (paper | arxiv | lab | repo |
    # book | dataset), not the librarian kind. Both are kept: ours fixes the
    # shape, theirs stays branchable in `origin`.
    origin = "generated" if generated else value(fm.get("kind"))

    title = (value(fm.get("title"))
             or first_heading(body, level=1)
             or path.stem)

    common = dict(
        repo="bd", path=rel, commit_sha=sha, kind="source",
        origin=origin,
        # A distillation is not itself evidence of anything -- it records what a
        # source says. The tier belongs to the claim that cites it, so
        # `evidence` stays empty here and `advances` is false by derivation.
        provenance=None if generated else "from_paper",
        reproduced=reproduced(fm.get("reproduced")),
        lab_authored=bool(fm.get("lab_authored")),
        has_falsifier=has_falsifier(text),
        doi=value(fm.get("doi")),
        conditions=value(fm.get("access")),
    )

    out = [Doc(locator=s.locator,
               title=f"{title} -- {s.title}" if s.title else title,
               body=s.body, **common)
           for s in sections(body)]
    if not out:
        out.append(Doc(locator="#", title=title, body="", **common))
    return out


def bd_source(root: Path, sha: str) -> list[Doc]:
    src = root / "knowledge" / "source"
    if not src.is_dir():
        raise FileNotFoundError(f"{src} does not exist")

    out: list[Doc] = []
    for path in sorted(src.rglob("*.md")):
        if not path.is_file() or path.name.startswith("."):
            continue
        out.extend(_doc_set(path, path.relative_to(root).as_posix(), sha))
    return out
