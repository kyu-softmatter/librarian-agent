"""Does what is declared still match what exists?

Six file-level checks, none of which needs an adapter -- which is why they run
over any repository in `cache/`, including ones with no adapter yet. That
matters for Phase 0's exit condition: the two defects a human found by hand are
in BD, and a tool that cannot rediscover them is not yet doing anything.

  gate_declared_not_implemented   a gate with a threshold in docs and no code
  generator_missing               a generated file naming a generator that is gone
  declared_count_mismatch         a generated index stating a count that is wrong
  falsifier_missing               an entry that therefore cannot be challenged
  tier_path_conflict              the folder says one tier, the frontmatter another
  review_expired                  review_after has passed
"""

from __future__ import annotations

import datetime as _dt
import re
from pathlib import Path

from librarian.doc import Finding
from librarian.md import frontmatter, has_falsifier

_GATE = re.compile(r"\bG\d+[a-z]?\b")
# A gate **declared** in a table row, not merely mentioned in prose.
_GATE_DECL_ROW = re.compile(r"^\|\s*\**(G\d+[a-z]?)\b", re.MULTILINE)
# `<!-- Generated: docs/tools/wiki_index.py -- do not edit by hand -->` and the
# Korean form BD actually uses.
_GENERATED = re.compile(
    r"(?:generated|생성됨)\s*[:：]\s*([\w./\\-]+\.(?:py|sh|js|ts))", re.IGNORECASE)
# `| 항목 수 | **40** |`  ·  `| entries | 40 |`
_COUNT_ROW = re.compile(
    r"^\|\s*(?:항목\s*수|entry\s+count|entries|count|items)\s*\|\s*\**(\d+)\**\s*\|",
    re.IGNORECASE | re.MULTILINE)

_GATE_KEY = lambda g: (int(re.sub(r"\D", "", g)), g)


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _gate_sets(root: Path) -> tuple[set[str], set[str]]:
    """Gates in code, and gates **declared** in a docs table.

    A prose mention is not a declaration, and conflating the two produces a
    whole class of false positives across repositories. Measured: BD's
    `docs/06-roadmap.md` discusses the handoff in prose -- *"G8 needs D or tau_c
    ... at that repo's G11"* -- referring to the **microscope's** gates. BD's own
    Python namespace is G0-G6 plus G100, so subtracting one from the other
    reported six of MS's gates as missing from BD.

    A table row is a declaration: it carries the threshold and the default
    verdict. MS `docs/04-decision-engine.md` has

        | G2 | Emission collection | `spectral_collection >= 15%` | ... | BLOCKED |

    so only row-leading gate ids count, which is what this check's own wording
    claims and previously did not verify.
    """
    py: set[str] = set()
    md: set[str] = set()
    for p in root.rglob("*.py"):
        if ".git" in p.parts:
            continue
        py |= set(_GATE.findall(_read(p)))
    docs = root / "docs"
    for p in (docs.rglob("*.md") if docs.is_dir() else []):
        md |= set(_GATE_DECL_ROW.findall(_read(p)))
    return py, md


def drift(root: Path, repo: str) -> list[Finding]:
    out: list[Finding] = []
    today = _dt.date.today()

    # 1. A gate declared with a threshold, implemented nowhere.
    py, md = _gate_sets(root)
    for g in sorted(md - py, key=_GATE_KEY):
        out.append(Finding(
            "gate_declared_not_implemented", f"{repo}:{g}",
            "declared in docs/ with a threshold and a default verdict, and "
            "named in no Python file", "error"))

    # 2-3. Generated artefacts: is the generator still there, and is the count right?
    for p in sorted(root.rglob("*.md")):
        if ".git" in p.parts:
            continue
        text = _read(p)
        rel = p.relative_to(root).as_posix()

        m = _GENERATED.search(text[:400])
        if m:
            gen = m.group(1).replace("\\", "/")
            if not (root / gen).exists():
                out.append(Finding(
                    "generator_missing", f"{repo}:{rel}",
                    f"header names {gen}, which is not in the repository, so the "
                    "file cannot be regenerated and says not to edit it", "error"))

            c = _COUNT_ROW.search(text)
            if c:
                declared = int(c.group(1))
                actual = sum(1 for s in p.parent.glob("*.md")
                             if s.name != p.name and not s.name.startswith("_"))
                if declared != actual:
                    out.append(Finding(
                        "declared_count_mismatch", f"{repo}:{rel}",
                        f"states {declared} entries; {actual} sibling files exist",
                        "error"))

    # 4-6. Per-entry checks over the stores that carry frontmatter.
    for store in ("kb", "knowledge"):
        base = root / store
        if not base.is_dir():
            continue
        for folder in sorted(p for p in base.iterdir() if p.is_dir()):
            mds = sorted(folder.glob("*.md"))
            entries = [p for p in mds if not p.name.startswith("_")
                       and p.name.lower() != "readme.md"]
            with_fals = [p for p in entries if has_falsifier(_read(p))]

            # The folder's convention is established by the **majority**, not by
            # the existence of two examples. Measured: 2 of 20 files in
            # `kb/decisions/` mention a falsification condition in passing, and a
            # >=2 threshold reported the other 18 as defective -- burying the one
            # finding that matters under noise. A decision log is not a claim
            # entry and owes no falsifier; `kb/expertise/` (5 of 6) does.
            share = len(with_fals) / len(entries) if entries else 0.0
            if len(entries) >= 3 and share >= 0.6:
                for p in entries:
                    if p in with_fals:
                        continue
                    out.append(Finding(
                        "falsifier_missing",
                        f"{repo}:{p.relative_to(root).as_posix()}",
                        f"{len(with_fals)} of {len(entries)} entries in "
                        f"{folder.name}/ carry a falsifier and this one does not, "
                        "so by kb-schema 4.7 it cannot be challenged", "warn"))

            for p in entries:
                fm, _ = frontmatter(_read(p))
                if not fm:
                    continue
                ev = fm.get("evidence")
                if folder.name == "literature" and ev == "measured":
                    out.append(Finding(
                        "tier_path_conflict", f"{repo}:{p.relative_to(root).as_posix()}",
                        "sits in literature/ but claims evidence: measured; a "
                        "literature value can never advance a verdict", "error"))
                if folder.name == "calibrations" and ev == "assumed":
                    out.append(Finding(
                        "tier_path_conflict", f"{repo}:{p.relative_to(root).as_posix()}",
                        "sits in calibrations/ but claims evidence: assumed", "error"))

                ra = str(fm.get("review_after") or "")
                if re.match(r"^\d{4}-\d{2}-\d{2}$", ra):
                    if _dt.date.fromisoformat(ra) < today:
                        out.append(Finding(
                            "review_expired", f"{repo}:{p.relative_to(root).as_posix()}",
                            f"review_after {ra} has passed", "warn"))
    return out
