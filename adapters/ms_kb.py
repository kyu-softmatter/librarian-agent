"""MS `kb/` -- seven stores, three different shapes.

The shapes differ and that is not untidiness: MS separates them by **how a value
was arrived at**, and the folder is part of the tier. `kb/calibrations/`
outranks `kb/literature/` by rule, not by convention, so the folder a file sits
in is read as evidence and cross-checked against its frontmatter.

  calibrations/  YAML list of measurement records   -> evidence: measured
  literature/    markdown + frontmatter (0 entries) -> evidence: assumed, always
  expertise/     markdown + frontmatter             -> evidence from frontmatter
  systems/       markdown, frontmatter on some      -> a dossier is a card
  decisions/     markdown, **no frontmatter**       -> date and slug come from the name
  plans/         markdown + frontmatter             -> evidence: None, always
  sessions/      markdown + frontmatter             -> evidence: None, always
  external/<origin>/  imported numbers, nested one level -> evidence: None

`external/` is the third, and MS wrote down why in
`kb/decisions/2026-09-15-numbers-from-another-repository.md`: a number computed
in the simulator, imported here, *"may motivate a design, and **no gate may
clear against them**."* Two rules from that decision are load-bearing for this
parse. **The path carries the foreignness** -- *"a frontmatter field does not
show at the citation site"*, and `kb/calibrations/` is refused outright because
that directory means measured-on-this-instrument. And
**`may_be_gate_threshold: false` is the default**. So these rows get
`kind="external"` rather than being filed as a card or a source, and
`evidence: None` like the other two.

`plans/` and `sessions/` are the two narrative stores that are **not** a tier. A plan is
a proposal for a run that has not happened and states its own unknowns as
BLOCKED; a session log is what a working day recorded, failures included.
Neither is a measurement, so neither gets one -- they are pinned to
`evidence: None` below rather than reading a tier out of frontmatter, because a
plan quoting a calibrated number is still a plan. They are indexed because they
are where the *question* a run exists to answer is written down, which nothing
else in `kb/` holds.
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
    "plans": "plan",
    "sessions": "session",
    "external": "external",
}

# The stores whose entries are never evidence, whatever their frontmatter says.
# `_md_docs` reads `evidence:` from frontmatter for every other folder; here the
# folder overrides it, which is the same rule as FOLDER_EVIDENCE running the
# other way.
FOLDER_NO_EVIDENCE = frozenset({"plans", "sessions", "external"})


def _external_conditions(fm: dict) -> str | None:
    """What an imported number may be used for, from its own frontmatter.

    `kb/external/` carries the terms in fields rather than in a `scope:` line,
    and they are the terms a caller has to see: which repository it came from,
    the coordinate and content hash it was taken at, and -- the one MS's
    decision calls hard rule 3 -- whether it may be a gate threshold. Carried
    as `conditions` so it travels with every hit, the way `return_always` does
    for a tier.
    """
    if not _value(fm.get("origin")):
        return None
    bits = [f"origin: {_value(fm.get('origin'))}"]
    for key in ("evidence_class", "source_ref", "source_hash", "thread"):
        v = _value(fm.get(key))
        if v:
            bits.append(f"{key}: {v}")
    gate = fm.get("may_be_gate_threshold")
    if gate is not None:
        bits.append(f"may_be_gate_threshold: {str(bool(gate)).lower()}")
    return " · ".join(bits)


def _md_docs(path: Path, rel: str, folder: str, sha: str) -> list[Doc]:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = frontmatter(text)
    falsifier = has_falsifier(text)

    if folder in FOLDER_NO_EVIDENCE:
        evidence = None
    else:
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
        # `source:` in `literature/`, `origin:` in `external/` -- different
        # folders, so neither shadows the other, and `external`'s value names
        # the repository the number came from.
        origin=_value(fm.get("source")) or _value(fm.get("origin")),
        evidence=evidence,
        tier=1 if evidence == "measured" else (3 if evidence == "assumed" else None),
        # An imported number was computed, not observed here. `derived` is the
        # one `PROVENANCE` value that says so -- `measurement` would claim the
        # thing MS's decision refuses, and leaving it unset would lose the only
        # branchable mark that the row is not this instrument's.
        provenance="derived" if folder == "external" else None,
        review_after=review,
        # `corrected_by` is MS's word for it in `kb/external/`, and it is the
        # same relation: a later round that replaces this one's numbers.
        superseded_by=(_value(fm.get("superseded_by_measurement"))
                       or _value(fm.get("superseded_by"))
                       or _value(fm.get("corrected_by"))),
        has_falsifier=falsifier,
        doi=_value(fm.get("doi")),
        conditions=_value(fm.get("scope")) or _external_conditions(fm),
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
        # **Recursive, to match how the coverage check already enumerates.**
        # `librarian/scan.py` globs `kb/` with `rglob`, so a nested store was
        # counted as a candidate and produced nothing -- which is what happened
        # to `external/bd/` the day MS created it: four files, one level down,
        # invisible to `iterdir()`. Every other store here is flat, so this
        # changes nothing for them and stops the next nested one being dropped.
        for path in sorted(d.rglob("*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            rel = path.relative_to(root).as_posix()
            if path.suffix in {".yaml", ".yml"}:
                out.extend(_yaml_docs(path, rel, folder, sha))
            elif path.suffix == ".md":
                out.extend(_md_docs(path, rel, folder, sha))
            # .txt / .reference are archived material, not entries
    return out
