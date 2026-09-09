"""BD's contract vocabulary, read from the contract rather than hard-coded.

`knowledge/wiki/CLAUDE.md` says it plainly: *"위 YAML frontmatter가 기계가 읽는
계약이고 (...) 코드는 경로를 하드코딩하지 말고 frontmatter를 파싱한다"* — the
frontmatter is the machine-readable contract, and code parses it instead of
hard-coding paths. So the declared type and kind vocabularies are read from that
file, and an undeclared value is carried through rather than dropped.

Two things here exist because YAML 1.1 is not JSON:

  `reproduced: yes` loads as the **boolean True**, not the string "yes", and
  `Doc.reproduced` takes BD's own three-value vocabulary. Left unmapped the
  field silently becomes invalid and every wiki page loses its reproduction
  state -- which is the one field BD's discipline section turns on, since
  `reproduced: no` may be cited as a record and never as grounds.

  An empty `confirmed_by:` key loads as None, and `str(None)` is `"None"`. A
  string that reads like a value is worse than an absent one.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from librarian.md import frontmatter

#: Where BD's wiki contract lives, relative to the checkout root.
CONTRACT = "knowledge/wiki/CLAUDE.md"

#: BD's wiki `type` -> the librarian kind. The three that have a kind of their
#: own keep it; the rest are subject cards, which is what MIGRATION.md 5 already
#: routes them to (`concepts/` -> 05-physics, `techniques/` -> 06-simulation,
#: `systems/` -> 06-simulation/cards/). BD's own type survives in `origin`, so
#: collapsing four types onto `card` loses nothing a caller can branch on.
TYPE_KIND = {
    "finding": "finding",
    "question": "question",
    "benchmark": "assumed",     # a validation oracle read out of the literature
    "concept": "card",
    "technique": "card",
    "system": "card",
}


def value(v: Any) -> str | None:
    """A frontmatter scalar as a string, with absence preserved as None."""
    if v is None or v is False:
        return None
    s = str(v).strip()
    return s or None


def reproduced(v: Any) -> str | None:
    """BD's `reproduced` as one of yes / no / partial.

    YAML 1.1 folds `yes`/`no` to booleans before this ever sees them, so the
    booleans are mapped back rather than rejected.
    """
    if v is True:
        return "yes"
    if v is False:
        return "no"
    s = str(v).strip().lower() if v is not None else ""
    return s if s in {"yes", "no", "partial"} else None


@lru_cache(maxsize=8)
def _contract_text(root: str) -> str:
    p = Path(root) / CONTRACT
    if not p.is_file():
        raise FileNotFoundError(f"{p} does not exist: BD's wiki contract is the schema")
    return p.read_text(encoding="utf-8", errors="replace")


def contract(root: Path) -> dict[str, Any]:
    """The parsed contract. Raises if it is absent -- there is no fallback.

    Guessing the vocabulary when the contract is missing would index BD against
    a schema nobody agreed to, and the guess would be invisible in the output.
    """
    fm, _ = frontmatter(_contract_text(str(root)))
    if not fm:
        raise ValueError(f"{CONTRACT} has no frontmatter to parse")
    return fm


def kind_for(root: Path, declared: str | None) -> str:
    """The librarian kind for a declared wiki `type`.

    A type the contract does not declare still gets indexed, as a card. The
    alternative is dropping it, and a silently dropped page is the failure this
    repository exists to catch -- `scan` reports it as `file_produced_nothing`
    only if nothing comes back at all.
    """
    if declared in TYPE_KIND:
        return TYPE_KIND[declared]
    return "card"
