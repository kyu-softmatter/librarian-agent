"""RT indexed -- and this repository's own citations made checkable.

`PLAN.md`, `BUILD.md`, `FEEDBACK.md`, `TREE.md` and every README here cite rt's
items as **grounds**: `C-001` for the self-confirming loop, `T-048` for what
makes a challenge a work order rather than an argument, `Q-010` for the missing
cost ceiling, `T-018` and `T-035` for *citations stay, attributions go*. The
prohibitions in this repository's own boundary table are stated to be
*"inherited, not chosen ... from the six philosophy items and the boundary table
in research-topic."*

**Until rt was indexed none of that resolved.** The ID was quoted and there was
nowhere to walk it back to, in a repository whose first invariant is that every
value is walkable back to a location. So the load-bearing test here is not that
the adapter parses -- it is that every rt item this repository leans on is
declared at a locator.
"""

import re
from collections import Counter
from pathlib import Path

import pytest

from adapters import ADAPTERS
from adapters.rt_ideas import KIND, rt_ideas
from librarian.scan import CANDIDATES, scan, sources_for

ROOT = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.integration


@pytest.fixture
def rt() -> Path:
    p = ROOT / "cache" / "rt"
    if not (p / ".git").exists():
        pytest.skip("cache/rt is not cloned")
    return p


#: An rt item id, **not** preceded by a repo prefix. rt's own rule is that
#: *"IDs from other repos carry a prefix: `BD:I-050` · `MS:G27`"*, and this
#: repository follows it -- so `BD:I-052` is a citation into the simulator and
#: not a claim about rt.
_CITED = re.compile(r"(?<![A-Za-z:`\-])([TCQ]-\d{3})\b")

#: This repository's own prose. `cache/` is other people's repositories and
#: `store/inbox/` holds drafts for another repository's folder.
def _own_docs() -> list[Path]:
    out = []
    for p in sorted(ROOT.rglob("*.md")):
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith(("cache/", ".venv/", "node_modules/")):
            continue
        out.append(p)
    return out


def test_every_rt_item_this_repository_cites_resolves(rt):
    """The point of connecting rt at all.

    A claim citing `C-001` as grounds and unable to name where `C-001` is
    declared is the shape of defect this index exists to make impossible. It is
    also the one that reads most like rigour: an ID looks like a citation.
    """
    declared = {d.locator for d in rt_ideas(rt, "s") if d.kind in KIND.values()}
    assert declared, "the ideas adapter found no items"

    missing: dict[str, list[str]] = {}
    for p in _own_docs():
        rel = p.relative_to(ROOT).as_posix()
        for m in _CITED.finditer(p.read_text(encoding="utf-8")):
            if m.group(1) not in declared:
                missing.setdefault(m.group(1), []).append(rel)

    assert missing == {}, (
        "cited as grounds and declared nowhere in rt: "
        + "; ".join(f"{k} ({', '.join(sorted(set(v))[:3])})"
                    for k, v in sorted(missing.items())))


def test_every_bd_idea_this_repository_cites_is_reachable(rt, tmp_path):
    """The same check for BD's ids -- and they resolve through rt, not BD.

    **BD's `design/ideas.md` was not in its public repository.** Measured
    2026-09-16 against the GitHub tree for `main`: 2,587 paths, no `design/`,
    and **no `I-NNN` token anywhere in the checkout**. Publishing it was decided
    the same day (PLAN.md §1.4c), so that is a record of a window. **This test
    does not change when the push lands** -- it asserts that each cited id is
    reachable, and an original is a better answer than a translation, not a
    different assertion. rt states that
    *"quotations from BD's Korean design documents are translated. The
    originals are findable by ID in that repo"* -- which does not hold for the
    public repo, whatever is on the author's disk.

    So the six BD ideas this repository cites as grounds -- `I-050`, `I-052`,
    `I-053`, `I-075`, `I-076`, `I-133` -- are reachable only through rt, which
    quotes and translates each with the BD id attached. That is a weaker
    citation than an original and it is a real one: `rt@sha:design/ideas.md#T-007`
    resolves and says what `I-052` claimed, while `bd:design/ideas.md#I-052`
    does not exist.

    This test is what keeps that true. Cite a seventh BD idea rt does not carry
    and it fails here, rather than the citation reading as grounds.
    """
    import re

    from librarian.gaps import gaps as compute_gaps
    from librarian.index import NEUTRAL, Index, build
    from librarian.links import extract
    from librarian.scan import scan

    cited: dict[str, set[str]] = {}
    for p in _own_docs() + [q for d in ("librarian", "adapters", "mcp_server")
                            for q in sorted((ROOT / d).rglob("*.py"))]:
        rel = p.relative_to(ROOT).as_posix()
        for m in re.finditer(r"\bI-\d{3}\b", p.read_text(encoding="utf-8")):
            cited.setdefault(m.group(0), set()).add(rel)
    assert cited, "this repository cites no BD ideas; the regex or the prose moved"

    rep = scan(rt)
    idx_path = tmp_path / "kb.sqlite"
    build(rep.docs, idx_path, {"rt": rep.sha},
          extract(rep.docs, rep.repo_files, rep.source_text), compute_gaps(rt))
    idx = Index(idx_path)
    try:
        unreachable = {k: sorted(v) for k in sorted(cited)
                       if not idx.search(k, NEUTRAL, limit=1).hits
                       for v in [cited[k]]}
    finally:
        idx.close()
    assert unreachable == {}, (
        "cited as grounds and reachable in neither repository: "
        + "; ".join(f"{k} ({', '.join(v[:2])})" for k, v in unreachable.items()))


def test_the_items_this_repository_leans_on_hardest_are_present(rt):
    """Named explicitly, because the test above passes vacuously if the
    adapter ever stops parsing and this repository stops citing at the same
    time. These ten are load-bearing in the design documents."""
    docs = {d.locator: d for d in rt_ideas(rt, "s")}
    for item, expect_kind in (("C-001", "finding"), ("C-005", "finding"),
                              ("C-007", "finding"), ("T-018", "decision"),
                              ("T-023", "decision"), ("T-034", "decision"),
                              ("T-035", "decision"), ("T-048", "decision"),
                              ("T-049", "decision"), ("Q-010", "question")):
        assert item in docs, item
        assert docs[item].kind == expect_kind, (item, docs[item].kind)
        assert docs[item].body.strip(), f"{item} has an empty body"


def test_a_prefixed_id_is_a_citation_out_and_not_an_rt_item(rt):
    """rt's own rule, and getting it wrong would file BD's ideas as rt's.

    `BD:I-052` appears in these cells constantly. An adapter matching any
    `X-000` would invent a declaration at a locator, which is worse than
    missing one: the citation would resolve, to the wrong repository.
    """
    items = [d for d in rt_ideas(rt, "s") if d.kind in KIND.values()]
    assert all(re.fullmatch(r"[TCQ]-\d{3}", d.locator) for d in items)
    text = (rt / "design" / "ideas.md").read_text(encoding="utf-8")
    assert "BD:`I-050`" in text, "the fixture for this test is that prefixes occur"
    assert not [d for d in items if d.locator.startswith(("I-", "G-"))]


def test_all_three_table_shapes_are_read(rt):
    """`| ID | Idea | Source | Status |` for `T-`, and a three-column
    `| ID | Conflict | Status |` / `| ID | Question | Status |` for the rest.

    Hard-coding four columns drops every conflict and every open question --
    which is half of what this repository cites, and it would fail silently
    because the rows simply would not appear.
    """
    kinds = Counter(d.kind for d in rt_ideas(rt, "s") if d.kind in KIND.values())
    assert kinds["decision"] > 0 and kinds["finding"] > 0 and kinds["question"] > 0
    assert kinds["finding"] >= 9 and kinds["question"] >= 10


def test_a_status_naming_another_item_becomes_a_supersession(rt):
    """*"Ideas are not deleted. Only their status changes."* So the link is in
    the status cell -- `transformed → T-018` -- and it is the only place the
    item graph is recorded."""
    docs = {d.locator: d for d in rt_ideas(rt, "s")}
    assert docs["C-002"].superseded_by == "T-018"
    assert docs["T-009"].superseded_by == "T-018"
    # A bare status is a status, not a supersession.
    assert docs["C-001"].superseded_by is None
    assert docs["C-001"].conditions and "open" in docs["C-001"].conditions.lower()


def test_every_item_carries_a_status_despite_six_malformed_rows(rt):
    """The defect this file has, and why the parser tolerates it.

    Six rows do not have the column count their own header declares: five
    conflict rows -- **`C-001`, `C-003`, `C-004`, `C-005`, `C-007`** -- are
    missing the pipe before their status, so `Open` trails the body cell; and
    `T-054` has two stray pipes inside its body. **Three of those five are
    among the items this repository cites most.**

    A conflict whose status is unknown reads exactly like one nobody recorded,
    so the status is recovered from the vocabulary the file declares for itself
    (*"`raw` -> `adopted` / `parked` / `rejected`"*, plus `Open` / `Closed`) and
    from nothing else.

    Asserted as a property rather than as the list of six, so it keeps holding
    when rt fixes the pipes -- which is the outcome to want.
    """
    items = [d for d in rt_ideas(rt, "s") if d.kind in KIND.values()]
    without = [d.locator for d in items if not d.conditions]
    assert without == [], f"no status recovered for {without}"
    for loc in ("C-001", "C-003", "C-004", "C-005", "C-007"):
        assert docs_of(items)[loc].conditions.lower().startswith("open")
    # And the recovered status is stripped out of the body it was trailing.
    assert not docs_of(items)["C-001"].body.rstrip().endswith("Open")


def test_two_sources_are_not_collapsed_into_one_provenance(rt):
    """`T-054`'s source cell is `[user] · [derived]`. Two sources is not one of
    `librarian.doc.PROVENANCE`'s values, and picking either would be this
    adapter deciding which one counts -- so `origin` keeps what the cell says
    and `provenance` stays unset."""
    docs = docs_of([d for d in rt_ideas(rt, "s") if d.kind in KIND.values()])
    assert docs["T-054"].origin == "user · derived"
    assert docs["T-054"].provenance is None
    assert (docs["T-001"].origin, docs["T-001"].provenance) == ("user", "declaration")
    assert (docs["T-002"].origin, docs["T-002"].provenance) == ("derived", "derived")


def docs_of(items):
    return {d.locator: d for d in items}


def test_the_two_personas_are_agents_with_their_pole(rt):
    """V1 and V2 are the two poles of a value axis and **disagree by
    construction** (`C-002`), which is why they are agents here in the same
    sense MS's lenses are -- and why `rt:V1` / `rt:V2` profiles will reach them
    through the same rows `profile_candidates` already reads."""
    from adapters.rt_design import rt_design
    agents = [d for d in rt_design(rt, "s") if d.kind == "agent"]
    assert {d.origin for d in agents} == {"V1", "V2"}
    assert all(d.path.startswith("design/personas/") for d in agents)


def test_nothing_from_rt_can_advance_a_verdict(rt):
    """rt's own rule, not a gap in the parse: `charter.md` §5 says this
    repository sets no values and runs nothing. A pass *condition* is a form;
    the number meeting it belongs to whoever measured or ran it."""
    docs = scan(rt).docs
    assert docs
    assert not any(d.advances for d in docs)
    assert {d.evidence for d in docs} == {None}


def test_rt_is_covered_and_selected_like_the_other_two(rt):
    """The convention, asserted as a correspondence rather than a list -- the
    same reason `test_candidate_enumeration_is_independent_of_the_adapters`
    exists. Adding rt's two sources should not have needed this file edited."""
    assert sources_for(rt) == [n for n in ADAPTERS if n.startswith("rt_")]
    assert set(sources_for(rt)) == {"rt_ideas", "rt_design"}
    for name in sources_for(rt):
        assert name in CANDIDATES, name

    rep = scan(rt)
    assert rep.per_source and all(n > 0 for n in rep.per_source.values())
    assert [f for f in rep.findings] == [], rep.findings
