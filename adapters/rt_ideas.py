"""RT `design/ideas.md` -- the item log, one document per ID.

**This is the adapter that makes this repository's own citations checkable.**
`PLAN.md`, `BUILD.md`, `FEEDBACK.md` and every README here cite rt's items as
grounds -- `C-001` for the self-confirming loop, `T-048` for what makes a
challenge a work order, `Q-010` for the missing cost ceiling, `T-018` and `T-035`
for citations-stay-attributions-go. Until this adapter existed **none of those
resolved**: the ID was quoted and there was nowhere to walk it back to.

So the locator is the ID itself, and a hit is `rt@sha:design/ideas.md#T-048`.

**The contract is declared in the file**, under *"Rules for this document"*, and
it is read rather than assumed:

  ideas are not deleted; only their status changes    -> `superseded_by`, where
    `raw` -> `adopted` / `parked` / `rejected`           a status names another ID
  numbers are not renumbered; gaps are intentional    -> no ordering is inferred
  IDs from other repos carry a prefix: `BD:I-050`     -> those are not rt items
  conflicts are marked, not resolved (`C-`), and         and are skipped
    the same for open questions (`Q-`)

**Three table shapes, and the header row is what distinguishes them** --
`| ID | Idea | Source | Status |` for `T-`, and a three-column
`| ID | Conflict | Status |` / `| ID | Question | Status |` for `C-` and `Q-`.
Hard-coding four columns drops every conflict and every open question, which is
half of what this repository cites.

**The prefix rule matters more than it looks.** `BD:I-052` appears in these
cells constantly, and it is a citation into another repository, not an item
declared here. An adapter that matched any `X-000` would file BD's ideas as rt's
own -- inventing a declaration, at a locator, which is the one failure this
index is built to make impossible.
"""

from __future__ import annotations

import re
from pathlib import Path

from librarian.doc import Doc
from librarian.md import sections

#: An rt item at the start of a table row. **Not preceded by a repo prefix** --
#: `BD:I-050` and `MS:G27` are citations out, per the file's own rule.
_ROW = re.compile(r"^\|\s*(?<![A-Za-z:])([TCQ]-\d{3})\s*\|", re.MULTILINE)

#: `| ID | Idea | Source | Status |` vs `| ID | Conflict | Status |`.
_HEADER = re.compile(r"^\|\s*ID\s*\|(.+?)\|\s*$", re.MULTILINE)

#: The status cell names another item: *"refined → `T-018`"*, *"transformed →
#: `T-018`"*. A bare `raw` / `Open` / `Closed` is a status, not a supersession.
_SUPERSEDED = re.compile(r"(?:→|->)\s*`?([TCQ]-\d{3})`?")

#: Each cell opens with the claim in bold, which is the title a reader scans for.
_LEAD = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)

#: The status vocabulary, from the file's own rules: *"Ideas are not deleted.
#: Only their status changes: `raw` -> `adopted` / `parked` / `rejected`"*, plus
#: the `Open` / `Closed` the conflict and question tables use.
#:
#: **Needed because six rows do not have the column count their header
#: declares.** Five conflict rows -- `C-001`, `C-003`, `C-004`, `C-005`,
#: `C-007` -- are missing the pipe before their status, so `Open` trails the
#: body cell; and `T-054` has two stray pipes inside its body, splitting it
#: into three cells. Three of the five are among the items this repository
#: cites most.
#:
#: Dropping the status on those rows would be defensible and useless: a
#: conflict whose status is unknown reads the same as one nobody recorded. So
#: the status is recovered from the declared vocabulary, and only from it --
#: never from an arbitrary trailing word.
_STATUS_WORDS = ("raw", "adopted", "parked", "rejected", "open", "closed")
_TRAILING_STATUS = re.compile(
    r"(?:\s|\*)(" + "|".join(_STATUS_WORDS) + r")\**\s*$", re.IGNORECASE)

KIND = {"T": "decision", "C": "finding", "Q": "question"}

#: The `Source` column, where the shape has one. `[user]` is a person stating
#: it; `[derived]` is read off another repository's design. Both are in
#: `librarian.doc.PROVENANCE`, so neither has to be invented here.
PROVENANCE = {"user": "declaration", "derived": "derived"}

#: A source cell holds one or more bracketed tokens: `[user]`, or
#: `[user] · [derived]` (`T-054`). **`provenance` is set only when there is
#: exactly one**, because two sources is not one of the two vocabulary values
#: and picking either would be this adapter deciding which one counts. `origin`
#: keeps what the cell says, verbatim.
_SOURCE_TOKEN = re.compile(r"\[([a-z]+)\]", re.IGNORECASE)


def _cells(line: str) -> list[str]:
    """The cells of one table row, pipes at both ends stripped."""
    parts = line.split("|")
    if len(parts) >= 2 and not parts[0].strip():
        parts = parts[1:]
    if parts and not parts[-1].strip():
        parts = parts[:-1]
    return [p.strip() for p in parts]


def _columns_for(text: str, pos: int) -> list[str]:
    """The header of the table this row is in -- the nearest one above it.

    Read per row rather than once per file: `ideas.md` holds five item tables
    in two shapes, and the last header before a row is the one that applies.
    """
    best: list[str] = []
    for m in _HEADER.finditer(text):
        if m.start() > pos:
            break
        best = ["ID"] + [c.strip() for c in m.group(1).split("|")]
    return best


def _split_row(cells: list[str], cols: list[str]) -> tuple[str, str, str]:
    """`(body, status, source)` from a row, tolerating a wrong column count.

    **The ID is always first and `Source`/`Status` are always last**, so a stray
    pipe can only be inside the body -- which is what makes the long case
    reconstructible rather than guessed. `T-054` carries
    `| [user] · [derived] | raw |` at the end and two stray pipes in the middle.

    The short case is the reverse: a missing pipe leaves the status inside the
    body cell, and it is recovered from the vocabulary the file declares for it.
    """
    n = len(cols)
    tail = [c for c in ("Source", "Status") if c in cols]
    if len(cells) > n and tail:
        # Stray pipes in the body: the tail columns keep their positions from
        # the end, and everything between the ID and them is one cell.
        body = "|".join(cells[1: len(cells) - len(tail)]).strip()
        rest = cells[len(cells) - len(tail):]
    else:
        body = cells[1].strip() if len(cells) > 1 else ""
        rest = cells[2:]

    got = dict(zip(tail, rest))
    status = got.get("Status", "").strip()
    source = got.get("Source", "").strip()

    if not status and "Status" in cols:
        m = _TRAILING_STATUS.search(body)
        if m:
            status = m.group(1)
            body = body[: m.start()].rstrip()
    return body, status, source


def rt_ideas(root: Path, sha: str) -> list[Doc]:
    path = root / "design" / "ideas.md"
    if not path.is_file():
        raise FileNotFoundError(f"{path} does not exist")
    rel = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")

    out: list[Doc] = []
    seen: set[str] = set()
    for m in _ROW.finditer(text):
        item = m.group(1)
        if item in seen:
            # Numbers are not renumbered, so a duplicate row means the file
            # changed shape -- report it by skipping rather than by emitting two
            # documents at one coordinate, which `scan` would call a collision.
            continue
        seen.add(item)

        line_end = text.find("\n", m.start())
        line = text[m.start(): line_end if line_end != -1 else len(text)]
        cells = _cells(line)
        cols = _columns_for(text, m.start())

        def cell(name: str) -> str:
            if name in cols:
                i = cols.index(name)
                if i < len(cells):
                    return cells[i]
            return ""

        body, status, source = _split_row(cells, cols)

        lead = _LEAD.search(body)
        sup = _SUPERSEDED.search(status)
        tokens = [t.lower() for t in _SOURCE_TOKEN.findall(source)]
        out.append(Doc(
            repo="rt", path=rel, locator=item, commit_sha=sha,
            kind=KIND[item[0]],
            origin=" · ".join(tokens) or None,
            provenance=PROVENANCE.get(tokens[0]) if len(tokens) == 1 else None,
            # An item is a design statement, never a measurement: rt sets no
            # values and runs nothing (charter.md §5), so no evidence tier can
            # apply and `advances` stays false by derivation.
            evidence=None,
            superseded_by=sup.group(1) if sup else None,
            conditions=status or None,
            title=f"{item}: {lead.group(1).strip() if lead else body[:80]}",
            body=body,
        ))

    # The prose around the tables carries the file's own contract -- the rules
    # quoted in this module's docstring are a section of it, and a claim about
    # how these items behave should be citable too.
    for s in sections(text):
        if not s.body.strip():
            continue
        out.append(Doc(
            repo="rt", path=rel, locator=s.locator, commit_sha=sha,
            kind="doc_section", provenance="declaration",
            title=f"ideas -- {s.title}" if s.title else "ideas",
            body=s.body,
        ))
    return out
