"""Markdown and YAML frontmatter helpers shared by the adapters.

Sections are the locator unit. A hit points at a section, not a file, because
"the paper says X" is only checkable if you are told where.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import yaml

_FM = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
# The contract is a **section**, not a word. MS's literature template makes
# `## Falsification conditions` mandatory and `kb/expertise/` follows it.
_FALSIFIER_HEADING = re.compile(r"falsif|would retire|would replace", re.IGNORECASE)
# A narrower prose fallback, for entries that state the condition without a
# heading. Bare "falsif" is deliberately not accepted here.
_FALSIFIER_PROSE = re.compile(
    r"falsification condition|would retire this|would replace this", re.IGNORECASE)


def frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split YAML frontmatter from the body. Missing frontmatter is not an error.

    MS's stores are mixed on purpose: `kb/expertise/` and `kb/systems/current.md`
    carry frontmatter, `kb/decisions/` does not. An adapter that required it
    would drop 20 decision records without saying so.
    """
    m = _FM.match(text)
    if not m:
        return {}, text
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}, text
    if not isinstance(data, dict):
        return {}, text
    return data, text[m.end():]


def slug(title: str) -> str:
    """A locator slug. ASCII only -- non-ASCII headings collapse to a digest.

    Korean headings exist in BD's corpus. Passing them through would produce
    exactly the filenames BD already broke (NFC/NFD splits the same name in two
    across macOS and Windows), so paths and locators stay ASCII while prose does
    not.
    """
    s = re.sub(r"[^a-zA-Z0-9]+", "-", title).strip("-").lower()
    if not s:
        import hashlib
        s = "h-" + hashlib.sha1(title.encode()).hexdigest()[:8]
    return s[:60]


@dataclass(frozen=True, slots=True)
class Section:
    level: int
    title: str
    locator: str
    body: str


def sections(body: str, min_level: int = 2) -> list[Section]:
    """Top-level sections of a markdown body.

    A body with no headings yields one whole-file section with locator '#', so
    every document has a coordinate.
    """
    heads = [m for m in _HEADING.finditer(body) if len(m.group(1)) <= min_level]
    if not heads:
        text = body.strip()
        return [Section(0, "", "#", text)] if text else []

    out: list[Section] = []
    preamble = body[: heads[0].start()].strip()
    if preamble:
        out.append(Section(0, "", "#", preamble))

    seen: dict[str, int] = {}
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(body)
        title = m.group(2).strip()
        loc = slug(title)
        if loc in seen:                      # duplicate headings do occur
            seen[loc] += 1
            loc = f"{loc}-{seen[loc]}"
        else:
            seen[loc] = 1
        out.append(Section(len(m.group(1)), title, loc,
                           body[m.end(): end].strip()))
    return out


def has_falsifier(text: str) -> bool:
    """Does this entry carry the check that would overturn it?

    Philosophy 3, and `kb-schema.md` 4.7 makes the consequence explicit: an entry
    with no falsifier **cannot be challenged**, and that is a defect in the entry
    rather than a gap in the mechanism. So this returning False is a finding, not
    a parse failure.

    **Frontmatter is excluded, and a heading is what counts.** Scanning the whole
    file for the word matched an entry whose own `id:` was `no-falsifier` --
    which is the failure this check exists to report, answered backwards.
    """
    _, body = frontmatter(text)
    if any(_FALSIFIER_HEADING.search(m.group(2)) for m in _HEADING.finditer(body)):
        return True
    return bool(_FALSIFIER_PROSE.search(body))


def first_heading(text: str) -> str:
    m = _HEADING.search(text)
    return m.group(2).strip() if m else ""
