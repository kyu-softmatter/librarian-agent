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
import os
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from librarian.doc import Doc, Finding, Gap
from librarian.links import Link

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

CREATE TABLE finding (
  check_name  TEXT NOT NULL,
  subject     TEXT NOT NULL,
  detail      TEXT NOT NULL,
  severity    TEXT NOT NULL
);

CREATE INDEX finding_check ON finding(check_name);

CREATE TABLE gap (
  registry      TEXT NOT NULL,
  entry         TEXT NOT NULL,
  field         TEXT NOT NULL,
  present       INTEGER NOT NULL,
  gate          TEXT,
  finding_code  TEXT,
  repo          TEXT NOT NULL
);

CREATE INDEX gap_field ON gap(field);
CREATE INDEX gap_gate ON gap(gate);

CREATE TABLE link (
  src_uid      TEXT NOT NULL,
  relation     TEXT NOT NULL,
  raw          TEXT NOT NULL,
  dst_path     TEXT,
  dst_locator  TEXT,
  dst_uid      TEXT,
  status       TEXT NOT NULL
);

CREATE INDEX link_src ON link(src_uid);
CREATE INDEX link_dst ON link(dst_uid);
CREATE INDEX link_status ON link(status);

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

def build(docs: Iterable[Doc], path: Path, repo_shas: dict[str, str],
          links: Iterable["Link"] = (), gaps: Iterable[Gap] = (),
          findings: Iterable[Finding] = ()) -> int:
    """Write the index from scratch. Never incremental.

    Sorted by uid before insert so two runs over the same input produce the same
    file, which is what makes the regeneration criterion checkable at all.

    **Built beside the target and moved in by `os.replace`.** It used to unlink
    the old file and create the new one in place, which left a window where the
    index was absent or half-built: `mcp_server.tools._open` returned `None` and
    a call arriving then got `status: no_index`. Honest, and avoidable -- the
    server opens the index read-only and **per call**, so with an atomic rename
    a caller gets the old index or the new one and never a missing one.

    This is the index's half of decision (j): the same rule the write tools
    follow for a record (`librarian/record.py`), applied to the one file this
    module writes. Two concurrent rebuilds still need no lock, because a
    rebuild is deterministic -- identical inputs give byte-identical output, so
    the race has no losing outcome, and differing inputs leave the last writer's
    index with `index_stale` telling the truth on the next call.
    """
    rows = sorted(docs, key=lambda d: d.uid)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Same directory, so the rename stays on one filesystem. The name carries a
    # uuid rather than the pid: two *threads* of one process building the same
    # target would otherwise share one temp path, and the second `connect` to a
    # database the first is writing fails with `attempt to write a readonly
    # database`. Written with the pid first, and the race test found it.
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")

    db = sqlite3.connect(tmp)
    try:
        db.executescript(_DDL)
        db.executemany(
            f"INSERT INTO doc ({','.join(_COLS)}) "
            f"VALUES ({','.join('?' * len(_COLS))})",
            [tuple(_cell(d, c) for c in _COLS) for d in rows],
        )
        db.executemany(
            "INSERT INTO finding (check_name, subject, detail, severity) "
            "VALUES (?, ?, ?, ?)",
            [(f.check, f.subject, f.detail, f.severity)
             for f in sorted(findings, key=lambda f: (f.check, f.subject))],
        )
        db.executemany(
            "INSERT INTO gap (registry, entry, field, present, gate, "
            "finding_code, repo) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(g.registry, g.entry, g.field, int(g.present), g.gate,
              g.finding_code, g.repo)
             for g in sorted(gaps, key=lambda g: (g.registry, g.field, g.entry))],
        )
        db.executemany(
            "INSERT INTO link (src_uid, relation, raw, dst_path, dst_locator, "
            "dst_uid, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(l.src_uid, l.relation, l.raw, l.dst_path, l.dst_locator,
              l.dst_uid, l.status) for l in links],
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
    try:
        os.replace(tmp, path)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
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
class ProfileCandidate:
    """A profile the question's own words point at -- and nothing more.

    It answers *"which profile should I have declared"* without deciding it.
    `because` is the uid of the **agent file** whose ownership section matched,
    never of the profile: a profile listing a term is this repository
    describing itself, while `.claude/agents/` is the owner's own declaration
    at a locator (PLAN.md 3.6, 5.3).
    """
    profile: str
    because: str                         # repo:path#locator of the agent doc
    declares: str                        # what that file says it owns, verbatim
    score: float
    #: The question's own words that licensed this candidate -- the discriminating
    #: ones only. A term every owner declares is dropped before it gets here.
    matched_terms: tuple[str, ...] = ()


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
    profile_candidates: list[ProfileCandidate] = field(default_factory=list)

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
            # Returned, and applied to nothing. The hits above were ranked by
            # the profile the caller declared; these say which profile the
            # question's own words point at, each citing the file that says so.
            # The caller chooses -- so the choice lands in the caller's
            # transcript, where it is visible (PLAN.md 5.3 rule 1).
            "profile_candidates": [
                {"profile": c.profile, "because": c.because,
                 "declares": c.declares, "matched_terms": list(c.matched_terms),
                 "score": round(c.score, 4)}
                for c in self.profile_candidates
            ],
            "candidates_applied": False,
        }


#: Function words, dropped before a question is matched against an owner's
#: declaration. They are the difference between this mechanism working and not:
#: an `owns` section is **prose**, so `can`, `this` and `the` occur in it as
#: ordinary words, and a question's stopwords then match a declaration for no
#: reason a caller could check. Measured before the list existed: *"how long can
#: I image this dye before it bleaches"* was licensed for lens 5 by `can` and
#: `this` -- the right answer for a reason that says nothing.
#:
#: **This is not the morphological analysis decision 7 rules out.** That rules
#: out a stemmer, on the grounds that reproducibility outranks ranking quality.
#: A fixed list in a versioned file is the opposite of a stemmer: it is
#: readable, diffable, and matches the same way on every machine.
#:
#: Used **only** for profile candidates. `search` does not consult it -- a
#: caller asking about `the` gets whatever bm25 says, and the hits are the
#: product this repository is judged on.
_STOPWORDS = frozenset("""
a about all also an and any are as at be been but by can could did do does
for from had has have how if in into is it its may more most must no not of
on one only or other out over own said same should so some such than that
the their them then there these they this those to too under up use used
using very was way we were what when where which while who why will with
would you your
""".split())


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

    # -- one document ------------------------------------------------------

    def get(self, uid: str) -> dict[str, Any] | None:
        """One document in full, with its outbound and inbound references.

        Returns None rather than raising: a uid that is not here is an answer.
        `near` names the other sections of the same file, because the usual
        reason a uid misses is that the locator moved when a heading was edited.
        """
        row = self.db.execute("SELECT * FROM doc WHERE uid = ?", (uid,)).fetchone()
        if row is None:
            path = uid.split("#", 1)[0].split(":", 1)[-1]
            near = [r["uid"] for r in self.db.execute(
                "SELECT uid FROM doc WHERE path = ? ORDER BY uid", (path,))]
            return None if not near else {"status": "not_found", "uid": uid,
                                          "near": near}
        d = dict(row)
        d["advances"] = row["evidence"] == "measured"
        d["has_falsifier"] = bool(row["has_falsifier"])
        d["lab_authored"] = bool(row["lab_authored"])
        d["status"] = "ok"
        d["links_out"] = [dict(r) for r in self.db.execute(
            "SELECT relation, raw, dst_uid, dst_path, status FROM link "
            "WHERE src_uid = ? ORDER BY relation, raw", (uid,))]
        d["links_in"] = [dict(r) for r in self.db.execute(
            "SELECT src_uid, relation FROM link WHERE dst_uid = ? "
            "ORDER BY src_uid", (uid,))]
        return d

    # -- the reference graph -----------------------------------------------

    def neighbors(self, uid: str, relation: str = "cites",
                  direction: str = "out") -> list[dict[str, Any]]:
        """Documents one hop away.

        `same_file` is computed rather than stored -- it is the file path, not a
        reference anyone wrote.
        """
        if direction not in {"out", "in", "both"}:
            raise ValueError(f"direction {direction!r}")
        if relation == "same_file":
            path = uid.split("#", 1)[0].split(":", 1)[-1]
            return [{"uid": r["uid"], "relation": "same_file", "title": r["title"],
                     "kind": r["kind"], "direction": "both"}
                    for r in self.db.execute(
                        "SELECT uid, title, kind FROM doc WHERE path = ? AND uid != ? "
                        "ORDER BY uid", (path, uid))]

        out: list[dict[str, Any]] = []
        if direction in {"out", "both"}:
            out += [dict(r, direction="out") for r in self.db.execute(
                "SELECT l.dst_uid AS uid, l.relation, l.status, d.title, d.kind "
                "FROM link l LEFT JOIN doc d ON d.uid = l.dst_uid "
                "WHERE l.src_uid = ? AND l.relation = ? "
                "ORDER BY IFNULL(l.dst_uid, l.raw)", (uid, relation))]
        if direction in {"in", "both"}:
            out += [dict(r, direction="in") for r in self.db.execute(
                "SELECT l.src_uid AS uid, l.relation, l.status, d.title, d.kind "
                "FROM link l JOIN doc d ON d.uid = l.src_uid "
                "WHERE l.dst_uid = ? AND l.relation = ? "
                "ORDER BY l.src_uid", (uid, relation))]
        return out

    # -- what a gate is waiting for ----------------------------------------

    def gaps(self, field: Optional[str] = None, gate: Optional[str] = None,
             missing_only: bool = False) -> list[dict[str, Any]]:
        """Registry coverage per (registry, field), rolled up.

        The ratio stays over the whole registry even when only unfilled rows are
        shown: "0 of 6" and "0 of 0" say different things.
        """
        sql = ["SELECT registry, field, gate, finding_code, "
               "sum(present) AS filled, count(*) AS total FROM gap WHERE 1=1"]
        params: list[Any] = []
        if field:
            sql.append("AND field = ?")
            params.append(field)
        if gate:
            sql.append("AND gate = ?")
            params.append(gate)
        sql.append("GROUP BY registry, field, gate, finding_code "
                   "ORDER BY filled, registry, field")
        rows = [dict(r) for r in self.db.execute(" ".join(sql), params)]
        if missing_only:
            rows = [r for r in rows if not r["filled"]]
        for r in rows:
            r["blocked"] = r["filled"] == 0
        return rows

    def supplies(self, name: str) -> dict[str, Any]:
        """What supplies a registry field, or what a gate is waiting for.

        `name` is either a field (`bleach_photons`) or a gate (`G10`). Both are
        answered from the same table because the question is the same one asked
        from either end.
        """
        is_gate = bool(re.fullmatch(r"G\d+[a-z]?", name))
        rolled = self.gaps(gate=name) if is_gate else self.gaps(field=name)
        entries = [dict(r) for r in self.db.execute(
            "SELECT registry, entry, field, present, gate FROM gap "
            f"WHERE {'gate' if is_gate else 'field'} = ? "
            "ORDER BY present, registry, entry", (name,))]
        docs = [dict(r) for r in self.db.execute(
            "SELECT uid, kind, evidence, tier, title FROM doc "
            "WHERE title GLOB ? OR body GLOB ? ORDER BY uid LIMIT 20",
            (f"*{name}*", f"*{name}*"))]
        return {
            "name": name,
            "asked_as": "gate" if is_gate else "field",
            "coverage": rolled,
            "entries": entries,
            "mentioned_in": docs,
            "status": ("blocked" if rolled and all(r["blocked"] for r in rolled)
                       else "partial" if rolled else "unknown"),
        }

    def broken_links(self) -> list[Finding]:
        """References whose target is not in the repository at all.

        `in_repo` is excluded: a reference to a file no adapter reads is not a
        defect, and reporting it is how a link checker becomes noise.
        """
        return [
            Finding("broken_cross_reference", f"{r['src_uid']} -> {r['raw']}",
                    f"{r['relation']} target {r['dst_path'] or r['raw']!r} is not "
                    "in the repository", "warn")
            for r in self.db.execute(
                "SELECT * FROM link WHERE status = 'missing' "
                "ORDER BY src_uid, raw")
        ]

    def findings(self, check: Optional[str] = None) -> list[dict[str, Any]]:
        """The drift report, as computed at build time.

        Stored rather than recomputed so the server needs the index and nothing
        else. A check that needs the source tree -- comparing a declared gate
        against the code -- cannot run at query time anyway, because by then the
        source may have moved and the index has not.
        """
        # `check` is a reserved word in SQLite, hence the quoting.
        sql = 'SELECT check_name AS "check", subject, detail, severity FROM finding'
        params: tuple = ()
        if check:
            sql += " WHERE check_name = ?"
            params = (check,)
        sql += " ORDER BY severity != 'error', check_name, subject"
        return [dict(r) for r in self.db.execute(sql, params)]

    def entry_defects(self) -> dict[str, Any]:
        """Facts the doc table answers on its own, without a stored finding.

        **`no_falsifier` is deliberately not here.** A first version listed every
        document with `has_falsifier = 0`, which reported all three calibration
        records -- a calibration *is* the measurement, and MS's convention places
        the falsifier in `kb/expertise/` -- and listed the one real case three
        times, once per section. `drift.py` already answers this correctly, by
        asking whether the folder's own majority carries one, and a second worse
        copy of a check is not a second check.
        """
        import datetime as _dt
        today = _dt.date.today().isoformat()
        expired = [dict(r) for r in self.db.execute(
            "SELECT uid, review_after FROM doc WHERE review_after IS NOT NULL "
            "AND review_after < ? ORDER BY review_after, uid", (today,))]
        return {"review_expired": expired}

    def link_counts(self) -> dict[str, int]:
        return {r["status"]: r["n"] for r in self.db.execute(
            "SELECT status, count(*) AS n FROM link GROUP BY status")}

    # -- retrieval ---------------------------------------------------------

    #: At most this many sections of one file in a result set, while a hit from
    #: another file is available. Measured: asked what limits how long a dye can
    #: be imaged, `kb/expertise/oil-objective-trapping-in-water.md` took three
    #: of six slots and the objective registry -- which the question needed --
    #: was pushed out. bm25 ranks sections independently and has no reason not
    #: to fill a page with one document.
    MAX_PER_PATH = 2

    def search(self, query: str, profile: "Profile", limit: int = 10,
               current_shas: Optional[dict[str, str]] = None,
               require: Optional[dict[str, list[str]]] = None,
               max_per_path: Optional[int] = None,
               profiles: Optional[dict[str, "Profile"]] = None) -> SearchResult:
        """Ranked hits under one profile.

        Pass `profiles` -- every profile the server knows -- to have the result
        also carry `profile_candidates`: which profile the question's own words
        point at. Omitted, the field is empty, and `profile_candidates()` below
        omits it when it recurses so the search for candidates does not search
        for candidates of its own.
        """
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

        cap = self.MAX_PER_PATH if max_per_path is None else max_per_path
        res.hits = [_hit(r, s, matched_by)
                    for s, r in _diversify(scored, limit, cap)]
        res.status = "ok"
        if profiles:
            res.profile_candidates = self.profile_candidates(query, profiles)
        return res

    #: The locators an agent file states its ownership at. `owns` is the
    #: section, `definition` the frontmatter description -- which is where MS
    #: writes the invocation clause, *"Invoke it when the user mentions
    #: photobleaching, phototoxicity, ... exposure dose"*, put there for
    #: exactly this purpose.
    #:
    #: **Not `gates`.** Only 3 of MS's 5 agent files name a gate in their
    #: description, and lens 5 -- one of the two v1 profiles -- names none: it
    #: named G10 alone, and MS removed G10 on 2026-09-09. Keyed on gates this
    #: returns nothing for the lens the corpus is best prepared for
    #: (PLAN.md 5.3 rule 3).
    OWNERSHIP_LOCATORS = ("owns", "definition")

    def profile_candidates(self, query: str, profiles: dict[str, "Profile"],
                           limit: int = 4) -> list[ProfileCandidate]:
        """Which profiles the question's own words point at, each with a citation.

        **A term licenses a candidate only where it does not match every
        owner.** That is the whole mechanism, and the first draft did not have
        it: matching the question as one OR-combined FTS query -- the way
        `search` does -- ranked *"how long can I image this dye before it
        bleaches"* under **lens 4** and *"what seed did that run use"* under
        lens 5. Over 1,446 documents bm25 and the profile weights hold
        stopwords down. Over the five agent files they do not: `how`, `this`
        and `run` are in all five declarations, so they decided the order.

        So each term is asked separately, and a term matched by every owner is
        dropped -- it states nothing about who owns the question. A term with
        one owner is worth a whole point, a term with two half of one. This is
        §3.6's rule arithmetically: *"report which lens declares `G10`"* is
        answerable because `G10` has one owner, and the same sentence about a
        term every lens declares would be true and useless.

        **Two rules, and the second is what makes a candidate defensible.** A
        term matched by every owner is dropped, and a candidate also needs at
        least one term with **exactly one** owner. That second rule is §3.6's
        sentence as arithmetic: *"report which lens declares `G10`"* is
        answerable because `G10` has one owner, and the same sentence about a
        term every lens declares would be true and useless.

        **The known limit, measured rather than assumed: an inflected word
        does not reach the declaration.** `_fts_expr` quotes a term as a
        phrase, so trigram matching needs a contiguous substring -- `bleach`
        finds `photobleaching` in 14 agent documents and **`bleaches` finds
        0**. Decision 7 rules out the stemmer that would bridge them, so *"how
        long can I image this dye before it bleaches"* returns **no
        candidate**. That is the honest outcome: an empty candidate list says
        the question's words match no owner uniquely, which is true, and is
        worth more than a suggestion whose stated reason is `can`.

        Searched under `NEUTRAL`, deliberately: ranking the search for a
        profile *by* a profile would let the declared one decide which others
        look plausible, and nothing in the answer would show it.

        A profile with no `lens` gets no candidate, which is the correct answer
        rather than a gap: `human:*` roles and this repository's own `lib/`
        slot have no agent file to cite, and rule 2 does not bend for them
        (PLAN.md 5.3 rule 4).
        """
        # profile -> the agent-doc key that would declare it. Both ends are
        # read off a file: `lens: 5` in the profile, "Committee Lens 5" in the
        # agent description, which `adapters/ms_agents.py` stores as `origin`.
        by_key: dict[str, list[str]] = {}
        for prof in profiles.values():
            if prof.lens is None or ":" not in prof.id:
                continue
            repo = prof.id.split(":", 1)[0]
            by_key.setdefault(f"{repo}:lens-{prof.lens}", []).append(prof.id)
        if not by_key:
            return []

        owners = self._ownership_docs()
        if not owners:
            return []

        long_, _ = _terms(query)
        scores: dict[str, float] = {}
        matched: dict[str, list[str]] = {}
        sole: set[str] = set()                       # owners licensed outright
        for term in dict.fromkeys(long_):            # de-duplicated, order kept
            if term.lower() in _STOPWORDS:
                continue
            hit_keys = {k for k, _ in self._ownership_matches(term, owners)}
            if not hit_keys:
                continue
            # Matched by every owner, it says nothing about which one owns the
            # question. **Only where there is more than one owner**: the rule
            # is that a term has to discriminate *among* owners, and with a
            # single indexed owner there is nothing to discriminate among, so
            # the rule is vacuous and must not fire. It did, and no candidate
            # could ever be produced against a one-lens index -- a boundary the
            # real five-lens corpus hid completely.
            if len(owners) > 1 and len(hit_keys) == len(owners):
                continue
            if len(hit_keys) == 1:
                sole |= hit_keys
            for k in hit_keys:
                scores[k] = scores.get(k, 0.0) + 1.0 / len(hit_keys)
                matched.setdefault(k, []).append(term)

        out: list[ProfileCandidate] = []
        for key, score in scores.items():
            if key not in sole:
                continue
            uid, declares = owners[key]
            for pid in by_key.get(key, ()):
                out.append(ProfileCandidate(
                    profile=pid, because=uid,
                    declares=declares, score=score,
                    matched_terms=tuple(matched[key])))
        # Ties break on the profile id, so one index answers one question the
        # same way twice.
        out.sort(key=lambda c: (-c.score, c.profile))
        return out[:limit]

    def _ownership_docs(self) -> dict[str, tuple[str, str]]:
        """`repo:origin` -> (uid, the text that declares what it owns).

        One row per owner, `owns` preferred over `definition` because it is
        the section written to answer this and the description is a paragraph
        that also says who to invoke alongside.
        """
        out: dict[str, tuple[str, str]] = {}
        rows = self.db.execute(
            f"SELECT uid, repo, origin, locator, title, body FROM doc "
            f"WHERE kind = 'agent' AND origin IS NOT NULL AND locator IN "
            f"({','.join('?' * len(self.OWNERSHIP_LOCATORS))})",
            list(self.OWNERSHIP_LOCATORS)).fetchall()
        for r in sorted(rows, key=lambda r: (r["uid"],)):
            key = f"{r['repo']}:{r['origin']}"
            text = (r["body"] or r["title"] or "").strip()
            if key not in out or r["locator"] == "owns":
                out[key] = (r["uid"], text)
        return out

    def _ownership_matches(self, term: str,
                           owners: dict[str, tuple[str, str]]
                           ) -> list[tuple[str, str]]:
        """The owners one term matches, through the same FTS path as a search."""
        uid_to_key = {uid: key for key, (uid, _) in owners.items()}
        rows = self.db.execute(
            "SELECT d.uid FROM doc_fts JOIN doc d ON d.rowid = doc_fts.rowid "
            "WHERE doc_fts MATCH ? AND d.kind = 'agent'",
            (_fts_expr([term]),)).fetchall()
        return [(uid_to_key[r["uid"]], r["uid"])
                for r in rows if r["uid"] in uid_to_key]


def _diversify(scored: list[tuple[float, sqlite3.Row]], limit: int,
               cap: int) -> list[tuple[float, sqlite3.Row]]:
    """Take in rank order, capping sections per file -- then backfill.

    The backfill matters: capping alone would return fewer results than exist,
    which trades one bad answer for another. Held-back hits are appended in
    their original order, so the cap only ever *reorders* a full result set.
    """
    if cap <= 0:
        return scored[:limit]
    taken: list[tuple[float, sqlite3.Row]] = []
    held: list[tuple[float, sqlite3.Row]] = []
    seen: dict[str, int] = {}
    for s, r in scored:
        if len(taken) >= limit:
            break
        n = seen.get(r["path"], 0)
        if n < cap:
            seen[r["path"]] = n + 1
            taken.append((s, r))
        else:
            held.append((s, r))
    if len(taken) < limit:
        taken += held[: limit - len(taken)]
    return taken


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
    #: The lens this profile serves, as the profile file declares it. It is
    #: what links a profile to the agent file that declares what that lens
    #: owns -- both ends stated in a file, neither inferred (PLAN.md 5.3).
    lens: Optional[int] = None
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
        if "id" not in d:
            raise ValueError(
                f"{path} has no `id`, so it is not a caller profile. "
                "Prefix a non-profile file with `_` to keep it out of this glob.")
        boost = d.get("boost") or {}
        return cls(
            id=str(d["id"]),
            lens=int(d["lens"]) if d.get("lens") is not None else None,
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
    """Every caller profile in a directory.

    Files beginning with `_` are not profiles -- the convention is the
    microscope's, for the same reason: `_field-aliases.yaml` sits beside them
    and is configuration of a different kind, and loading it as a profile
    raised a `KeyError` on a missing `id` rather than saying so.
    """
    out = {NEUTRAL.id: NEUTRAL}
    for p in sorted(directory.glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        prof = Profile.load(p)
        out[prof.id] = prof
    return out
