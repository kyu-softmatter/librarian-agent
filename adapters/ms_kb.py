"""MS `kb/` -- five stores, three different shapes.

The shapes differ and that is not untidiness: MS separates them by **how a value
was arrived at**, and the folder is part of the tier. `kb/calibrations/`
outranks `kb/literature/` by rule, not by convention, so the folder a file sits
in is read as evidence and cross-checked against its frontmatter.

  calibrations/  YAML list of measurement records   -> evidence: measured
  literature/    markdown + frontmatter (0 entries) -> evidence: assumed, always
  expertise/     markdown + frontmatter             -> evidence from frontmatter
  systems/       markdown, frontmatter on some      -> a dossier is a card
  decisions/     markdown, **no frontmatter**       -> date and slug come from the name
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from librarian.doc import Doc
from librarian.md import first_heading, frontmatter, has_falsifier, sections

_DATED = re.compile(r"^(\d{4}-\d{2}-\d{2})[-_](.+)$")
_PLACEHOLDER = re.compile(r"\A<.*>\Z", re.DOTALL)


def _value(v):
    """A template placeholder is an absence marker, not a value.

    `kb/literature/_template.md` carries `review_after: <YYYY-MM-DD>` and
    `doi: "10.<...>"`. MS's own rule is that *"files beginning with `_` are not
    entries"*, but the template is still worth indexing -- it is the form a new
    entry has to fill, and the crosswalk writes into it. So the file is read and
    its placeholders are read as empty, which is what they mean.
    """
    if v is None:
        return None
    s = str(v).strip()
    if not s or _PLACEHOLDER.match(s) or "<" in s and ">" in s:
        return None
    return s

# The folder is the tier. Where frontmatter also states one, the two are
# cross-checked rather than one silently winning.
FOLDER_EVIDENCE = {
    "calibrations": "measured",
    "literature": "assumed",
}
FOLDER_KIND = {
    "calibrations": "calibration",
    "literature": "literature_form",
    "expertise": "expertise",
    "systems": "system",
    "decisions": "decision",
}


def _md_docs(path: Path, rel: str, folder: str, sha: str) -> list[Doc]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = frontmatter(text)
    falsifier = has_falsifier(text)

    evidence = _value(fm.get("evidence")) or FOLDER_EVIDENCE.get(folder)
    if evidence not in {"measured", "assumed", "confirmed_default", None}:
        evidence = None

    review = _value(fm.get("review_after"))
    # A level-1 heading, else what the frontmatter declares. `question` is the
    # better title where it exists -- MS's expertise entries state the question
    # the entry answers, which is what a reader is scanning for.
    title = (first_heading(body, level=1)
             or _value(fm.get("question"))
             or _value(fm.get("id"))
             or path.stem)

    common = dict(
        repo="ms", path=rel, commit_sha=sha, kind=FOLDER_KIND[folder],
        origin=_value(fm.get("source")),
        evidence=evidence,
        tier=1 if evidence == "measured" else (3 if evidence == "assumed" else None),
        review_after=review,
        superseded_by=_value(fm.get("superseded_by_measurement")),
        has_falsifier=falsifier,
        doi=_value(fm.get("doi")),
        conditions=_value(fm.get("scope")),
    )

    out = []
    for s in sections(body):
        out.append(Doc(locator=s.locator,
                       title=f"{title} -- {s.title}" if s.title else title,
                       body=s.body, **common))
    if not out:                                    # frontmatter-only file
        out.append(Doc(locator="#", title=title, body="", **common))
    return out


def _yaml_docs(path: Path, rel: str, folder: str, sha: str) -> list[Doc]:
    """A calibration file is a list of records, one measurement each."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace"))
    except yaml.YAMLError as e:
        raise ValueError(f"{rel}: {e}") from e

    records = data if isinstance(data, list) else [data]
    out = []
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            continue
        # `verified` is the measurer's own flag; it does not change the tier,
        # because the folder already fixed it. It is carried as provenance so a
        # caller can tell a cross-checked measurement from a bare one.
        out.append(Doc(
            repo="ms", path=rel, locator=f"{i}", commit_sha=sha,
            kind="calibration",
            evidence="measured", tier=1,
            provenance="measurement" if rec.get("verified") else None,
            origin=str(rec.get("measured_by")) if rec.get("measured_by") else None,
            title=str(rec.get("property") or rec.get("adapter") or f"{path.stem}[{i}]"),
            body=yaml.safe_dump(rec, allow_unicode=True, sort_keys=True),
        ))
    return out


def ms_kb(root: Path, sha: str) -> list[Doc]:
    kb = root / "kb"
    if not kb.is_dir():
        raise FileNotFoundError(f"{kb} does not exist")

    out: list[Doc] = []
    for folder, kind in FOLDER_KIND.items():
        d = kb / folder
        if not d.is_dir():
            continue
        for path in sorted(d.iterdir()):
            if not path.is_file() or path.name.startswith("."):
                continue
            rel = path.relative_to(root).as_posix()
            if path.suffix in {".yaml", ".yml"}:
                out.extend(_yaml_docs(path, rel, folder, sha))
            elif path.suffix == ".md":
                out.extend(_md_docs(path, rel, folder, sha))
            # .txt / .reference are archived material, not entries
    return out
