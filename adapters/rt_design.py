"""RT `README.md` + `design/` -- the form, the boundary, and the two personas.

Everything in this repository that is *inherited rather than chosen* comes from
here. `README.md` §2 has the three axes and the objection to the whole loop;
`charter.md` §3 is **the boundary table** -- ownership is fixed, the direction of
a work order is not -- and §5 is the list of what rt does not do;
`kb-schema.md` §4.1-4.7 fixes the seven entry kinds, one of which
(`kb_challenge_raise`'s) this repository implements.

    "The prohibitions are inherited, not chosen. They come from the six
     philosophy items and the boundary table in research-topic."
                                                 -- this repository's README

Indexed so that sentence can be checked.

**Two personas, and they are agents in the same sense MS's lenses are.** V1
(frontier) and V2 (unfinished) are the two poles of a value axis and they
**disagree by construction** (`C-002`) -- so they get `kind=agent` with `origin`
naming the pole, exactly as `ms_agents.py` records a lens number. That is what
lets `profile_candidates` reach them the day `rt:V1` and `rt:V2` profiles exist
(`PLAN.md` §5.1), from the same index rows and with the same citation.

**`design/ideas.md` is deliberately not read here** -- `adapters/rt_ideas.py`
owns it, because its unit is a table row with an ID rather than a section, and
that ID is what this repository cites.

**Nothing here carries an evidence tier, and that is rt's own rule**, not a gap
in the parse: `charter.md` §5 says this repository sets no values and runs
nothing. A pass *condition* is a form; the number that meets it belongs to
whoever measured or ran it.
"""

from __future__ import annotations

import re
from pathlib import Path

from librarian.doc import Doc
from librarian.md import first_heading, frontmatter, sections

#: `personas/V1-frontier.md` -> `V1`. The pole is in the filename because
#: rt's own `lineages.md` keys on it.
_PERSONA = re.compile(r"^(V\d)-")

#: Files the ideas adapter owns, and files that are not content.
SKIP = {"ideas.md"}


def _docs_for(path: Path, root: Path, sha: str) -> list[Doc]:
    rel = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = frontmatter(text)

    m = _PERSONA.match(path.name)
    persona = m.group(1) if m else None
    kind = "agent" if persona else "doc_section"
    title = first_heading(body, level=1) or path.stem

    out = []
    for s in sections(body):
        if not s.body.strip():
            continue
        out.append(Doc(
            repo="rt", path=rel, locator=s.locator, commit_sha=sha,
            kind=kind,
            origin=persona,
            # A persona file and a design document are both declarations. The
            # distinction that matters is `kind`, not provenance.
            provenance="declaration",
            title=f"{title} -- {s.title}" if s.title else title,
            body=s.body,
        ))
    if not out:
        out.append(Doc(
            repo="rt", path=rel, locator="#", commit_sha=sha, kind=kind,
            origin=persona, provenance="declaration", title=title, body=""))
    return out


def rt_design(root: Path, sha: str) -> list[Doc]:
    out: list[Doc] = []
    readme = root / "README.md"
    if readme.is_file():
        out += _docs_for(readme, root, sha)

    design = root / "design"
    if not design.is_dir():
        raise FileNotFoundError(f"{design} does not exist")
    for path in sorted(design.rglob("*.md")):
        if path.name in SKIP:
            continue
        # `_common.md` is **not** skipped. The leading underscore marks a
        # non-entry in MS's `kb/`, and rt uses it for the opposite thing: the
        # contract both personas inherit, including §3's vacated slot and §7's
        # unanswered "who computes `shared`". A convention read across
        # repositories without checking is how a store loses its own rules.
        out += _docs_for(path, root, sha)
    return out
