"""The search index: derived, deterministic, and honest about what it did not find.

Three decisions are load-bearing.

**Trigram, with a LIKE fallback for short terms.** Measured in `BUILD.md` 3:
`unicode61` returns 0 on a Korean substring, and `trigram` returns 0 on any
two-character term -- including `NA`, which is among the most-used terms in the
microscope's domain. Neither wins, so terms of three characters or more go to
`MATCH` (which carries bm25 ranking) and shorter ones go to `GLOB` (which is
exact and unranked).

`GLOB` rather than `LIKE`, because SQLite's `LIKE` is case-insensitive for ASCII
and `%NA%` therefore matched **349 of 544 documents** -- every `internal`,
`analysis` and `nothing` in the corpus. `GLOB '*NA*'` matches 65. For a
two-character technical term, case is the signal: `NA` is the numerical
aperture and `na` is a syllable.

**No timestamps.** `BUILD.md` 4-A requires that deleting `index/` and `map/` and
rebuilding produces byte-identical output, and a `built_at` breaks that for no
information gained: the commit SHA already identifies what the index was built
from, which is the question staleness actually asks.

**`advances` is not a column.** It is `evidence = 'measured'` in SQL, for the
same reason it is a property on `Doc` -- a stored copy can disagree with its
source, and that disagreement is the shape of an accident BD paid for.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from librarian.doc import Doc

SCHEMA_VERSION = "1"
MIN_MATCH_CHARS = 3          # below this, FTS5 trigram cannot form a token
_GLOB_ESCAPE = str.maketrans({"*": "[*]", "?": "[?]", "[": "[[]"})

_DDL = """
PRAGMA page_size = 4096;

CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE doc (
  uid            TEXT PRIMARY KEY,
  repo           TEXT NOT NULL,
  path           TEXT NOT NULL,
  locator        TEXT NOT NULL,
  commit_sha     TEXT NOT NULL,
  kind           TEXT NOT NULL,
  origin         TEXT,
  evidence       TEXT,
  tier           INTEGER,
  provenance     TEXT,
  reproduced     TEXT,
  lab_authored   INTEGER NOT NULL,
  review_after   TEXT,
  superseded_by  TEXT,
  has_falsifier  INTEGER NOT NULL,
  doi            TEXT,
  title          TEXT NOT NULL,
  body           TEXT NOT NULL,
  conditions     TEXT
);

CREATE INDEX doc_kind ON doc(kind);
CREATE INDEX doc_path ON doc(path);

CREATE VIRTUAL TABLE doc_fts USING fts5(
  title, body, conditions,
  content = 'doc', content_rowid = 'rowid',
  tokenize = 'trigram'
);
"""

_COLS = ("uid", "repo", "path", "locator", "commit_sha", "kind", "origin",
         "evidence", "tier", "provenance", "reproduced", "lab_authored",
         "review_after", "superseded_by", "has_falsifier", "doi",
         "title", "body", "conditions")


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def build(docs: Iterable[Doc], path: Path, repo_shas: dict[str, str]) -> int:
    """Write the index from scratch. Never incremental.

    Sorted by uid before insert so two runs over the same input produce the same
    file, which is what makes the regeneration criterion checkable at all.
    """
    rows = sorted(docs, key=lambda d: d.uid)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    db = sqlite3.connect(path)
    try:
        db.executescript(_DDL)
        db.executemany(
            f"INSERT INTO doc ({','.join(_COLS)}) "
            f"VALUES ({','.join('?' * len(_COLS))})",
            [tuple(_cell(d, c) for c in _COLS) for d in rows],
        )
        # An external-content FTS table is populated from its content table, so
        # the two cannot drift apart by construction.
        db.execute("INSERT INTO doc_fts(doc_fts) VALUES ('rebuild')")
        db.executemany(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            sorted({"schema_version": SCHEMA_VERSION,
                    "doc_count": str(len(rows)),
                    **{f"repo_sha:{k}": v for k, v in repo_shas.items()}}.items()),
        )
        db.commit()
    finally:
        db.close()
    return len(rows)


def _cell(d: Doc, col: str) -> Any:
    v = getattr(d, col)
    return int(v) if isinstance(v, bool) else v


def manifest(repo_shas: dict[str, str], doc_count: int) -> str:
    """The staleness reference. No timestamp, for the reason given above."""
    return json.dumps(
        {"schema_version": SCHEMA_VERSION, "doc_count": doc_count,
         "repo_sha": dict(sorted(repo_shas.items()))},
        indent=2, sort_keys=True) + "\n"


# --------------------------------------------------------------------------
# search
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Hit:
    uid: str
    score: float
    kind: str
    evidence: Optional[str]
    tier: Optional[int]
    has_falsifier: bool
    title: str
    snippet: str
    conditions: Optional[str]
    review_after: Optional[str]
    matched_by: str                     # match | like | match+like

    @property
    def advances(self) -> bool:
        return self.evidence == "measured"


@dataclass
class SearchResult:
    status: str                          # ok | searched_empty
    query: str
    profile: str
    index_sha: dict[str, str]
    index_stale: bool
    hits: list[Hit] = field(default_factory=list)
    terms_matched: list[str] = field(default_factory=list)
    terms_globbed: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "query": self.query,
            "caller_profile": self.profile,
            "index_sha": self.index_sha,
            "index_stale": self.index_stale,
            "terms": {"match": self.terms_matched, "glob": self.terms_globbed},
            "hits": [
                {"uid": h.uid, "score": round(h.score, 4), "kind": h.kind,
                 "evidence": h.evidence, "tier": h.tier, "advances": h.advances,
                 "has_falsifier": h.has_falsifier, "matched_by": h.matched_by,
                 "title": h.title, "conditions": h.conditions,
                 "review_after": h.review_after, "snippet": h.snippet}
                for h in self.hits
            ],
        }


def _terms(query: str) -> tuple[list[str], list[str]]:
    """Split a query into terms FTS5 can index and terms it cannot.

    Single characters are dropped. They are noise in a question -- the `I` in
    *"how long can I image this dye"* -- and with substring matching they match
    almost everything, so they cost precision and buy nothing.
    """
    long_, short = [], []
    for t in query.split():
        t = t.strip(".,;:()[]<>?!\"'")
        if len(t) < 2:
            continue
        (long_ if len(t) >= MIN_MATCH_CHARS else short).append(t)
    return long_, short


def _fts_expr(terms: list[str]) -> str:
    """OR the terms, and quote each one.

    **OR, not AND.** FTS5 defaults to AND, and under a trigram tokenizer that
    means every word of a question has to appear as a substring. Measured: *"what
    limits how long I can image this dye"* returned exactly one document out of
    544. bm25 already favours a document matching more of the query, so OR
    ranks rather than refuses.

    Quoting is not cosmetic: a bare query is FTS5 syntax, and `NA 1.45` raises.
    """
    return " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)


class Index:
    def __init__(self, path: Path):
        self.path = path
        self.db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        self.db.row_factory = sqlite3.Row
        self.meta = {r["key"]: r["value"] for r in self.db.execute("SELECT * FROM meta")}

    @property
    def repo_shas(self) -> dict[str, str]:
        return {k.split(":", 1)[1]: v for k, v in self.meta.items()
                if k.startswith("repo_sha:")}

    def is_stale(self, current: dict[str, str]) -> bool:
        """Stale when any indexed repo has moved on.

        Reported on every response. `BUILD.md` 4-D: deferring the weekly job
        moves the refresh to a human, so the defence has to move with it -- cron
        keeps a refresh from being forgotten, this keeps a forgotten one from
        being hidden.
        """
        held = self.repo_shas
        return any(held.get(k) != v for k, v in current.items())

    def close(self) -> None:
        self.db.close()

    # -- retrieval ---------------------------------------------------------

    def search(self, query: str, profile: "Profile", limit: int = 10,
               current_shas: Optional[dict[str, str]] = None,
               require: Optional[dict[str, list[str]]] = None) -> SearchResult:
        long_, short = _terms(query)
        res = SearchResult(
            status="searched_empty", query=query, profile=profile.id,
            index_sha=self.repo_shas,
            index_stale=self.is_stale(current_shas or {}),
            terms_matched=long_, terms_globbed=short,
        )
        if not long_ and not short:
            return res

        sql = ["SELECT d.*, "]
        params: list[Any] = []
        if long_:
            sql.append("bm25(doc_fts, 3.0, 1.0, 2.0) AS bm25 "
                       "FROM doc_fts JOIN doc d ON d.rowid = doc_fts.rowid "
                       "WHERE doc_fts MATCH ?")
            params.append(_fts_expr(long_))
        else:
            sql.append("0.0 AS bm25 FROM doc d WHERE 1=1")

        for t in short:
            pat = f"*{t.translate(_GLOB_ESCAPE)}*"
            sql.append("AND (d.title GLOB ? OR d.body GLOB ? OR "
                       "IFNULL(d.conditions,'') GLOB ?)")
            params += [pat] * 3

        for col, allowed in (require or {}).items():
            if col not in _COLS:
                raise ValueError(f"cannot require unknown column {col!r}")
            sql.append(f"AND d.{col} IN ({','.join('?' * len(allowed))})")
            params += allowed

        rows = self.db.execute(" ".join(sql), params).fetchall()
        if not rows:
            return res

        matched_by = "match+glob" if long_ and short else ("match" if long_ else "glob")
        scored = [(profile.score(r, bool(long_)), r) for r in rows]
        # Ties break on uid, so the same index answers the same question the
        # same way -- an oracle over an unstable order tests nothing.
        scored.sort(key=lambda sr: (-sr[0], sr[1]["uid"]))

        res.hits = [_hit(r, s, matched_by) for s, r in scored[:limit]]
        res.status = "ok"
        return res


def _hit(r: sqlite3.Row, score: float, matched_by: str) -> Hit:
    body = r["body"] or ""
    return Hit(
        uid=r["uid"], score=score, kind=r["kind"],
        evidence=r["evidence"], tier=r["tier"],
        has_falsifier=bool(r["has_falsifier"]),
        title=r["title"], conditions=r["conditions"],
        review_after=r["review_after"],
        snippet=" ".join(body.split())[:220],
        matched_by=matched_by,
    )


# --------------------------------------------------------------------------
# profiles
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Profile:
    """A versioned query profile. Not a query the LLM composes each time.

    BD `I-053`: perspective separation is produced not by separate stores but by
    a different search query per persona -- so a large corpus costs nothing in
    context, because it is an index and not context.
    """
    id: str
    kind_weight: dict[str, float] = field(default_factory=dict)
    boost_gate: tuple[str, ...] = ()
    boost_field: tuple[str, ...] = ()
    boost_path: tuple[str, ...] = ()
    demote: dict[str, dict[str, float]] = field(default_factory=dict)
    return_always: tuple[str, ...] = ()

    BOOST = 0.5

    def score(self, r: sqlite3.Row, ranked: bool) -> float:
        # bm25 is negative and lower is better; flip it so bigger is better.
        base = -float(r["bm25"]) if ranked else 1.0
        base = max(base, 1e-6)
        base *= self.kind_weight.get(r["kind"], 1.0)

        haystack = f"{r['title']}\n{r['body']}\n{r['conditions'] or ''}"
        bumps = 0.0
        if any(g in haystack for g in self.boost_gate):
            bumps += self.BOOST
        if any(f in haystack for f in self.boost_field):
            bumps += self.BOOST
        if any(r["path"].startswith(p) for p in self.boost_path):
            bumps += self.BOOST
        base *= 1.0 + bumps

        for col, table in self.demote.items():
            base *= table.get(str(r[col]), 1.0)
        return base

    @classmethod
    def load(cls, path: Path) -> "Profile":
        import yaml
        d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        boost = d.get("boost") or {}
        return cls(
            id=str(d["id"]),
            kind_weight={str(k): float(v) for k, v in (d.get("kind_weight") or {}).items()},
            boost_gate=tuple(boost.get("gate") or ()),
            boost_field=tuple(boost.get("field") or ()),
            boost_path=tuple(boost.get("path_prefix") or ()),
            demote={str(c): {str(k): float(v) for k, v in t.items()}
                    for c, t in (d.get("demote") or {}).items()},
            return_always=tuple(d.get("return_always") or ()),
        )


NEUTRAL = Profile(id="neutral")


def load_profiles(directory: Path) -> dict[str, Profile]:
    out = {NEUTRAL.id: NEUTRAL}
    for p in sorted(directory.glob("*.yaml")):
        prof = Profile.load(p)
        out[prof.id] = prof
    return out
