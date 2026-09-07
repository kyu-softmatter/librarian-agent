"""Does what is declared still match what exists?

Seven file-level checks, none of which needs an adapter -- which is why they run
over any repository in `cache/`, including ones with no adapter yet. That
matters for Phase 0's exit condition: the two defects a human found by hand are
in BD, and a tool that cannot rediscover them is not yet doing anything.

  gate_declared_not_implemented   a gate with a threshold in docs and no code
  gate_not_traceable_to_code      a gate with code that never names it
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
# `G1–G4`, `G20-G22`: one cell naming a span rather than each id. En-dash is
# what MS actually writes; hyphen and em-dash cost nothing to accept.
_GATE_SPAN = re.compile(r"\bG(\d+)\s*[-–—]\s*G?(\d+)\b")
# A backticked dotted path -- `optics.gate.evaluate`. Anchored on an identifier
# start so a threshold cell like `< 0.7 ×` cannot look like a symbol.
_DOTTED = re.compile(r"`([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)`")
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


def _defines(text: str, attr: str) -> bool:
    return re.search(rf"^\s*(?:async\s+def|def|class)\s+{re.escape(attr)}\b",
                     text, re.MULTILINE) is not None


def _symbol_exists(root: Path, dotted: str) -> bool:
    """Does `optics.gate.evaluate` name something that is actually here?

    Resolved by looking, never by importing -- the stance `generator_missing`
    already takes toward its generator. A repository under `cache/` is a
    foreign checkout with its own dependencies, and importing it would run its
    module bodies to answer a question about a name.

    Where the module path stops and the attribute starts is not known in
    advance -- `gate` is a module in MS and could be a package elsewhere -- so
    every split is tried, longest module path first.
    """
    parts = dotted.split(".")
    for i in range(len(parts) - 1, 0, -1):
        mod, attr = parts[:i], parts[i]
        for cand in (root.joinpath(*mod).with_suffix(".py"),
                     root.joinpath(*mod) / "__init__.py"):
            if cand.is_file() and _defines(_read(cand), attr):
                return True
    return False


def _gate_impls(root: Path) -> dict[str, tuple[str, str]]:
    """Gate id -> (the symbol that implements it, the docs file saying so).

    MS `docs/04-decision-engine.md` carries an implementation-status table
    beside its threshold table:

        | G1–G4 | `optics.gate.evaluate` | ✅ covered by tests |

    That row answers a question id-subtraction cannot ask. `optics/gate.py`
    implements all four of those gates and names none of them -- it states its
    checks as questions -- so `md - py` reported four gates as having no code
    while the code sat one directory away, at error severity. G1 escaped only
    because four unrelated modules happen to mention it while allocating ids
    (*"G1-G19 were taken by lenses 1/2/3/4/6/7"*), which is not implementation
    either.

    A row is believed only as far as it can be checked: the symbol has to
    resolve to a definition in this repository, or the row is ignored and the
    gate is still reported as unimplemented. A docs table asserting a function
    that does not exist earns no credit here.
    """
    out: dict[str, tuple[str, str]] = {}
    docs = root / "docs"
    for p in sorted(docs.rglob("*.md") if docs.is_dir() else []):
        rel = p.relative_to(root).as_posix()
        for line in _read(p).splitlines():
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) < 2:
                continue
            ids = set(_GATE.findall(cells[0]))
            for lo, hi in _GATE_SPAN.findall(cells[0]):
                if int(lo) <= int(hi):
                    ids |= {f"G{n}" for n in range(int(lo), int(hi) + 1)}
            if not ids:
                continue
            for m in _DOTTED.finditer(" ".join(cells[1:])):
                if _symbol_exists(root, m.group(1)):
                    for g in ids:
                        out.setdefault(g, (m.group(1), rel))
                    break
    return out


def drift(root: Path, repo: str) -> list[Finding]:
    out: list[Finding] = []
    today = _dt.date.today()

    # 1. A gate declared with a threshold and not named in code. Two different
    #    facts, and reporting them as one overstated the weaker: nothing
    #    implements it at all (error), or something does and no code says which
    #    gate it is (warn -- a traceability gap, not a missing gate).
    py, md = _gate_sets(root)
    impl = _gate_impls(root)
    for g in sorted(md - py, key=_GATE_KEY):
        where = impl.get(g)
        if where:
            sym, rel = where
            out.append(Finding(
                "gate_not_traceable_to_code", f"{repo}:{g}",
                f"declared in docs/ with a threshold, implemented by {sym} per "
                f"{rel}, and named in no Python file -- so no code says which "
                "gate it is", "warn"))
        else:
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
