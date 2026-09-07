"""The one normalized row every adapter produces.

Branchable fields are validated against closed vocabularies; prose fields are
not validated at all. That split is the whole point of the type — `kb/README.md`
states the rule, and this is where it is enforced rather than asked for.

`advances` is a property, not a field. A stored boolean could disagree with
`evidence`, and that disagreement is the shape of an accident BD paid for: it
filed `T = 300 K` as measured when it was a choice, propagating -4% to -14% into
every downstream tau_B. Derived, the disagreement cannot be represented.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Optional

REPOS = frozenset({"librarian", "ms", "bd", "rt"})

KINDS = frozenset({
    # canonical knowledge
    "card", "measured", "assumed", "finding", "question", "decision", "source",
    # MS store kinds, kept as-is until migration reclassifies them
    "expertise", "calibration", "system", "literature_form",
    # machine-readable inputs
    "registry", "doc_section", "agent",
    # Librarian's own
    "challenge", "retrieval",
})

EVIDENCE = frozenset({"measured", "assumed", "confirmed_default"})
PROVENANCE = frozenset({
    "from_drawing", "from_paper", "from_knowledge", "assumed", "derived",
    "measurement", "declaration",
})
REPRODUCED = frozenset({"yes", "no", "partial"})

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SLUG_OK = re.compile(r"^[\x20-\x7e]+$")          # printable ASCII


class DocError(ValueError):
    """A row that would have entered the index in a shape the design forbids."""


# `slots=True` is deliberately absent. Combined with `frozen=True` it makes an
# assignment raise `TypeError: super(type, obj): obj must be an instance or
# subtype of type` instead of `FrozenInstanceError` -- the protection holds, but
# the message names the wrong problem, and a misleading error costs more here
# than the bytes slots would save on a few hundred rows.


@dataclass(frozen=True)
class Doc:
    # --- coordinates: every row is walkable back to a source location -------
    repo: str
    path: str
    locator: str
    commit_sha: str

    # --- branchable --------------------------------------------------------
    kind: str
    origin: Optional[str] = None
    evidence: Optional[str] = None
    tier: Optional[int] = None
    provenance: Optional[str] = None
    reproduced: Optional[str] = None
    lab_authored: bool = False
    review_after: Optional[str] = None
    superseded_by: Optional[str] = None
    has_falsifier: bool = False
    doi: Optional[str] = None

    # --- prose: no code branches on these ---------------------------------
    title: str = ""
    body: str = ""
    conditions: Optional[str] = None

    def __post_init__(self) -> None:
        if self.repo not in REPOS:
            raise DocError(f"repo {self.repo!r} not in {sorted(REPOS)}")
        if self.kind not in KINDS:
            raise DocError(f"kind {self.kind!r} not in {sorted(KINDS)}")
        for name, vocab in (("evidence", EVIDENCE), ("provenance", PROVENANCE),
                            ("reproduced", REPRODUCED)):
            v = getattr(self, name)
            if v is not None and v not in vocab:
                raise DocError(f"{name} {v!r} not in {sorted(vocab)}")

        # Coordinates are mandatory. A hit that cannot be walked back is not
        # returned, so it must not be representable either (PLAN.md 3.1).
        if not self.path:
            raise DocError("path is empty")
        if "\\" in self.path:
            raise DocError(f"path {self.path!r} uses a backslash; paths are posix")
        if not self.locator:
            raise DocError(f"{self.path}: locator is empty (use '#' for whole-file)")
        if not _SLUG_OK.match(self.locator):
            raise DocError(f"locator {self.locator!r} is not printable ASCII")
        if not self.commit_sha:
            raise DocError(f"{self.path}: commit_sha is empty")

        if self.review_after is not None and not _DATE.match(self.review_after):
            raise DocError(f"review_after {self.review_after!r} is not YYYY-MM-DD")
        if self.tier is not None and not isinstance(self.tier, int):
            raise DocError(f"tier {self.tier!r} is not an integer")

    @property
    def uid(self) -> str:
        return f"{self.repo}:{self.path}#{self.locator}"

    @property
    def advances(self) -> bool:
        """Only a measurement may advance a verdict. Derived, never stored."""
        return self.evidence == "measured"

    def with_(self, **kw) -> "Doc":
        return replace(self, **kw)


@dataclass(frozen=True)
class Gap:
    """One registry field that a gate consumes, and whether it is there.

    Not a Doc: a gap is a statement about absence, and absence has no locator
    to be walked back to.
    """
    repo: str
    registry: str            # data/fluorophores.yaml
    entry: str               # AlexaFluor488
    field: str               # bleach_photons
    present: bool
    gate: Optional[str] = None          # G10
    finding_code: Optional[str] = None  # missing.bleach_photons

    @property
    def uid(self) -> str:
        return f"{self.repo}:{self.registry}#{self.entry}.{self.field}"


@dataclass(frozen=True)
class Finding:
    """One drift or defect report row. `check` is an enum; `detail` is prose."""
    check: str
    subject: str
    detail: str
    severity: str = "warn"   # warn | error

    def __post_init__(self) -> None:
        if self.severity not in {"warn", "error"}:
            raise DocError(f"severity {self.severity!r}")
