"""BD `knowledge/entries/*.json` -- `bdbot.kb_entry/0.1`, one lesson at a time.

**The decomposition key is the `lessons` array, and it is why this is 1 -> N
rather than a file move.** Measured on the current checkout it is 1 -> 1: all
144 entries carry exactly one lesson. That is a fact about today's corpus, not
about the schema, so the adapter iterates the array and gives each lesson its
own coordinate -- `lessons.0`, `lessons.1`. Writing it as one document per file
would work now and silently drop the second lesson the first time one is added.

`origin` is carried through unchanged because MIGRATION.md 5 routes these files
by it (`tooling` and `method` to `map/04-agents` or `06-simulation`, `handbook`
derived from `07-sources/books`, `intake` to `06-simulation`, `paper` to
`07-sources`). Collapsing it would throw away the migration key.

Three fields are empty for every entry in the current checkout -- `run_id`,
`case` and `outcome` -- which is the shape BD's own `tools/kb.py` accident left
behind: it *"simply reported 'run-less knowledge 0' for 126 existing entries."*
They are read anyway rather than assumed absent, so the day one is populated it
appears without a code change.

**`not_verified` is prose, and prose is not state.** It is a list of sentences
saying what about the claim has not been checked ("우리 시뮬레이션으로 재현하지
않았다 (tier 2)"), populated on 12 of 144. It reads like `reproduced` and is
not: `reproduced` is a three-value enum a caller may branch on, and this is a
caveat written for a human. So it lands in `conditions`, which nothing branches
on, and `reproduced` stays empty rather than being inferred from it.
"""

from __future__ import annotations

import json
from pathlib import Path

from librarian.doc import Doc

from ._bd import value

#: A lesson taken from a book or a paper carries that provenance. The other
#: three origins are our own tooling and method notes, and BD's vocabulary has
#: no term for them that would not be a guess -- so provenance stays empty
#: rather than being invented.
_ORIGIN_PROVENANCE = {"handbook": "from_paper", "paper": "from_paper"}

_SCHEMA = "bdbot.kb_entry/0.1"


def _title(lesson: dict, entry: dict, stem: str) -> str:
    """The lesson's own kind, then the claim. Long claims are the norm here."""
    claim = value(lesson.get("claim")) or ""
    head = claim.split(". ")[0][:140] if claim else ""
    kind = value(lesson.get("kind"))
    if head and kind:
        return f"[{kind}] {head}"
    return head or value(entry.get("source")) or stem


def _body(lesson: dict, entry: dict) -> str:
    """The claim, then everything a reader needs to weigh it.

    `source` is BD's own coordinate into its repository -- a path with a
    locator, e.g. `bdbot/constants.py#module-docstring`. It is kept verbatim in
    the body so the claim can be walked back one further hop than this index
    reaches on its own.
    """
    parts = [value(lesson.get("claim")) or ""]
    for label, key in (("source", "source"), ("run_id", "run_id"),
                       ("case", "case"), ("outcome", "outcome")):
        v = value(entry.get(key))
        if v:
            parts.append(f"{label}: {v}")
    tags = entry.get("system_tags")
    if isinstance(tags, list) and tags:
        parts.append("system_tags: " + " ".join(str(t) for t in tags))
    for key in ("dimensionless", "coords"):
        v = lesson.get(key) if key == "coords" else entry.get(key)
        if isinstance(v, dict) and v:
            parts.append(f"{key}: " + json.dumps(v, ensure_ascii=False, sort_keys=True))
    return "\n\n".join(p for p in parts if p)


def _conditions(entry: dict) -> str | None:
    nv = entry.get("not_verified")
    if isinstance(nv, list) and nv:
        return " · ".join(str(x).strip() for x in nv if str(x).strip()) or None
    return value(nv)


def bd_entries(root: Path, sha: str) -> list[Doc]:
    entries = root / "knowledge" / "entries"
    if not entries.is_dir():
        raise FileNotFoundError(f"{entries} does not exist")

    out: list[Doc] = []
    for path in sorted(entries.glob("*.json")):
        rel = path.relative_to(root).as_posix()
        try:
            entry = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError as e:
            raise ValueError(f"{rel}: {e}") from e
        if not isinstance(entry, dict):
            continue

        declared = value(entry.get("schema"))
        if declared and declared != _SCHEMA:
            # Read it anyway, and say so in the origin. A schema bump that
            # silently produced zero documents is the failure mode this
            # repository was built to report.
            origin_suffix = f" (schema {declared})"
        else:
            origin_suffix = ""

        origin = value(entry.get("origin"))
        lessons = entry.get("lessons")
        if not isinstance(lessons, list):
            continue

        for i, lesson in enumerate(lessons):
            if not isinstance(lesson, dict):
                continue
            out.append(Doc(
                repo="bd", path=rel, locator=f"lessons.{i}", commit_sha=sha,
                kind="finding",
                origin=(origin + origin_suffix) if origin else (origin_suffix or None),
                provenance=_ORIGIN_PROVENANCE.get(origin or ""),
                title=_title(lesson, entry, path.stem),
                body=_body(lesson, entry),
                conditions=_conditions(entry),
            ))
    return out
