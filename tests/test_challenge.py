"""`kb_challenge_raise`: the work order, and the four things that make it one.

The schema is research-topic's (`design/kb-schema.md` §4.7), so the vocabularies
here are quoted rather than designed. What this file asserts is that the two
rules that document calls load-bearing are enforced and not merely stated:
`falsifier_cited` points into the target, and routing reads the falsifier's type
and nothing else.
"""

import asyncio
import json

import pytest

from librarian.challenge import (ROUTES, STATES, ChallengeError, challenge,
                                 depth_of, open_against, record_id, write)
from librarian.doc import Doc
from librarian.index import build

TARGET = "ms:kb/expertise/oil-objective-trapping-in-water.md#verdict"
FALSIFIER = "ms:kb/expertise/oil-objective-trapping-in-water.md#falsification-conditions"
DATE = "2026-09-15"
HAS_FALSIFIER = {"has_falsifier": True}


def _chal(**kw):
    base = dict(target_uid=TARGET, doubt_kind="superseded_by_measurement",
                falsifier_cited=FALSIFIER,
                caller_profile="ms:lens-4-sample-optics",
                target=HAS_FALSIFIER)
    return challenge(**{**base, **kw})


# --- what makes it a work order ---------------------------------------------

def test_a_falsifier_outside_the_target_is_refused():
    """`T-048`'s prohibited move: a challenge may not cite a new basis.

    It reintroduces `C-005` -- a natural-language mass of counter-argument in
    the slot `personas/_common.md` §3 was vacated to empty. Checkable here
    because a uid carries its own file: the citation has to share the target's
    `repo:path`.
    """
    with pytest.raises(ChallengeError, match="prohibited move"):
        _chal(falsifier_cited="ms:kb/literature/some-other-paper.md#verdict")
    with pytest.raises(ChallengeError, match="prohibited move"):
        _chal(falsifier_cited="bd:knowledge/source/papers/x.md#falsification")
    # A different locator in the same file is exactly what is wanted.
    assert _chal()["falsifier_cited"] == FALSIFIER


def test_an_entry_with_no_falsifier_cannot_be_challenged():
    """*"A defect in the entry, and not a gap here."*

    Philosophy ③: every judgment carries the check that would overturn it. The
    refusal says where the fix goes -- a pull request against the repository
    that holds the entry -- because otherwise it reads as this tool being
    unable to do its job.
    """
    with pytest.raises(ChallengeError, match="defect in the entry"):
        _chal(target={"has_falsifier": False})
    with pytest.raises(ChallengeError, match="defect in the entry"):
        _chal(target={})


def test_a_target_absent_from_the_index_is_refused():
    with pytest.raises(ChallengeError, match="not in the index"):
        _chal(target=None)


def test_a_falsifier_that_does_not_resolve_is_refused():
    """The usual cause is an edited heading, so the refusal says so."""
    with pytest.raises(ChallengeError, match="edited heading"):
        _chal(falsifier_exists=False)


# --- routing ----------------------------------------------------------------

def test_routing_reads_the_falsifier_type_and_nothing_else():
    """Four doubt kinds name a resolver and the routing is a lookup on them."""
    expected = {
        "superseded_by_measurement": ("ms_experiment", "ms"),
        "contradicted_by_run": ("bd_run", "bd"),
        "conditions_not_met": ("literature", "research-topic"),
        "scope_exceeded": ("not_resolvable", "human"),
        "never_verified": ("not_resolvable", "human"),
    }
    assert ROUTES == expected
    for kind, (resolvable, routed) in expected.items():
        rec = _chal(doubt_kind=kind)
        assert (rec["resolvable_by"], rec["routed_to"]) == (resolvable, routed)


def test_the_sender_changes_nothing_about_the_route():
    """*"Routing is decided by the falsifier's type, not the sender."*

    Asserted by routing the same doubt from every caller: a challenge raised by
    the microscope against a claim it holds still goes to the microscope if
    that is what the falsifier needs, which is the case that would break if
    anything read `raised_by`.
    """
    routes = set()
    for profile in ("ms:lens-4-sample-optics", "ms:lens-5-photo-perturbation",
                    "bd:s3", "research-topic:V1", "neutral"):
        rec = _chal(caller_profile=profile, doubt_kind="contradicted_by_run")
        routes.add(rec["routed_to"])
        assert rec["raised_by"] == profile.split(":")[0]
    assert routes == {"bd"}, routes


def test_nothing_reads_raised_by():
    """Recorded and never branched on -- the same check as `note`."""
    import ast
    import pathlib

    import librarian.challenge as ch

    tree = ast.parse(pathlib.Path(ch.__file__).read_text(encoding="utf-8"))

    def mentions(node) -> bool:
        return any(
            (isinstance(sub, ast.Constant) and sub.value == "raised_by")
            or (isinstance(sub, ast.Name) and sub.id == "raised_by")
            for sub in ast.walk(node))

    offenders = [ast.dump(n)[:80] for n in ast.walk(tree)
                 if isinstance(n, (ast.Compare, ast.If)) and mentions(n)]
    assert offenders == [], offenders


def test_never_verified_gets_no_route_because_it_names_none():
    """The other four doubt kinds say what would settle them; this one says only
    that nothing has. Picking an instrument or a model for it would be a guess,
    and routing by guess is what "never by the sender" exists to prevent."""
    rec = _chal(doubt_kind="never_verified")
    assert rec["routed_to"] == "human"
    assert rec["resolvable_by"] == "not_resolvable"


def test_a_free_text_doubt_kind_is_refused():
    with pytest.raises(ChallengeError, match="cannot be free text"):
        _chal(doubt_kind="i think this is wrong")


# --- the state it is written in ---------------------------------------------

def test_it_settles_nothing_on_the_way_in():
    """`upheld`/`rejected` comes from a run, a measurement or a search -- never
    from a vote (BD `I-052`)."""
    rec = _chal()
    assert rec["state"] == "routed" and rec["state"] in STATES
    assert rec["resolved_by"] is None
    assert "upheld" not in json.dumps(rec) and "verdict" not in rec


def test_raised_is_unreachable_and_that_is_deliberate():
    """Routing is a lookup that completes before the record exists, so there is
    no moment at which a challenge here has a target and no route."""
    for kind in ROUTES:
        assert _chal(doubt_kind=kind)["state"] != "raised"
    assert "raised" in STATES, "it stays in the vocabulary; rt's schema owns it"


def test_cost_is_recorded_as_three_numbers():
    """*"Unrecorded, the budget stops being a budget and becomes the retirement
    decision."*"""
    rec = _chal(cost={"instrument_hours": 1.5})
    assert rec["cost"] == {"gpu_hours": 0.0, "instrument_hours": 1.5,
                           "search_budget_spent": 0.0}
    assert _chal()["cost"] == {"gpu_hours": 0.0, "instrument_hours": 0.0,
                               "search_budget_spent": 0.0}


# --- depth ------------------------------------------------------------------

def test_depth_increments_and_then_escalates_to_a_person(tmp_path):
    """`T-049`: without the bound the loop circulates doubt instead of topics.

    It **escalates rather than refuses**, because a refusal loses the challenge
    and escalation keeps it — and a person is the same damping device the
    `not_resolvable` route already uses.
    """
    first = write(tmp_path, _chal(doubt_kind="contradicted_by_run"), DATE)
    assert _chal(doubt_kind="contradicted_by_run")["depth"] == 0

    d1 = _chal(doubt_kind="contradicted_by_run",
               in_reply_to=record_id(first), prior_depth=0)
    assert d1["depth"] == 1 and d1["routed_to"] == "bd"

    d3 = _chal(doubt_kind="contradicted_by_run",
               in_reply_to=record_id(first), prior_depth=2)
    assert d3["depth"] == 3
    assert d3["routed_to"] == "human" and d3["escalated_at_depth"] == 2


def test_depth_is_read_from_the_record_it_replies_to(tmp_path):
    rec = _chal()
    w = write(tmp_path, rec, DATE)
    assert depth_of(tmp_path, record_id(w)) == 0
    assert depth_of(tmp_path, "chal-deadbeef") is None


def test_challenges_already_standing_are_reported(tmp_path):
    """Two records for one work order is how a queue of work becomes a queue of
    opinions, so a caller is shown the doubt already filed."""
    write(tmp_path, _chal(doubt_kind="contradicted_by_run"), DATE)
    write(tmp_path, {**_chal(doubt_kind="scope_exceeded"), "state": "rejected"}, DATE)
    standing = open_against(tmp_path, TARGET)
    assert [r["doubt_kind"] for r in standing] == ["contradicted_by_run"]
    assert open_against(tmp_path, "ms:kb/expertise/other.md#verdict") == []


# --- through the MCP surface ------------------------------------------------

@pytest.fixture
def writing_server(tmp_path):
    from mcp.server.mcpserver import MCPServer

    from mcp_server import tools
    docs = [
        Doc(repo="ms", path="kb/expertise/oil-objective-trapping-in-water.md",
            locator="verdict", commit_sha="s1", kind="expertise",
            has_falsifier=True, title="oil objective, water sample"),
        Doc(repo="ms", path="kb/expertise/oil-objective-trapping-in-water.md",
            locator="falsification-conditions", commit_sha="s1",
            kind="expertise", has_falsifier=True, title="-- Falsification"),
        Doc(repo="ms", path="kb/systems/no-falsifier.md", locator="verdict",
            commit_sha="s1", kind="system", title="a dossier with no falsifier"),
    ]
    idx = tmp_path / "kb.sqlite"
    build(docs, idx, {"ms": "s1"})
    cdir = tmp_path / "challenge"
    s = MCPServer(name="t", version="0")
    tools.register(s, index_path=idx, profiles_dir=tmp_path / "profiles",
                   challenge_dir=cdir)
    return s, cdir


def _call(server, name, args):
    res = asyncio.run(server.call_tool(name, args))
    assert res.is_error is False, f"{name} errored"
    return res.structured_content


def test_the_tool_writes_a_routed_work_order(writing_server):
    s, cdir = writing_server
    out = _call(s, "kb_challenge_raise", {
        "target_uid": TARGET, "doubt_kind": "superseded_by_measurement",
        "falsifier_cited": FALSIFIER,
        "caller_profile": "ms:lens-4-sample-optics",
        "instrument_hours": 2})
    assert out["status"] == "ok" and out["created"] is True
    assert out["id"].startswith("chal-")
    assert out["routed_to"] == "ms" and out["state"] == "routed"
    assert out["already_standing"] == []
    assert "falsifier's type" in " ".join(out["notes"])

    rec = json.loads(next(cdir.glob("*.json")).read_text(encoding="utf-8"))
    assert rec["target"] == {
        "repo": "ms",
        "entry": "kb/expertise/oil-objective-trapping-in-water.md",
        "claim": "verdict"}
    assert rec["cost"]["instrument_hours"] == 2.0
    assert "id" not in rec, "identity is the filename's digest"


def test_the_literature_route_settles_only_the_locator(writing_server):
    """The one thing this repository settles, and it answers a weaker question
    than the challenge asked. rt considered this escape and did not adopt it;
    here it is adopted, because it keeps the gate deterministic (`C-007`)."""
    s, _ = writing_server
    out = _call(s, "kb_challenge_raise", {
        "target_uid": TARGET, "doubt_kind": "conditions_not_met",
        "falsifier_cited": FALSIFIER})
    assert out["routed_to"] == "research-topic"
    assert out["locator_exists"] is True
    assert out["verdict"] == "unknown"
    assert any("C-007" in n for n in out["notes"])


def test_an_entry_without_a_falsifier_is_refused_at_the_surface(writing_server):
    s, cdir = writing_server
    out = _call(s, "kb_challenge_raise", {
        "target_uid": "ms:kb/systems/no-falsifier.md#verdict",
        "doubt_kind": "scope_exceeded",
        "falsifier_cited": "ms:kb/systems/no-falsifier.md#falsification"})
    assert out["status"] == "refused"
    assert "defect in the entry" in out["detail"]
    assert list(cdir.glob("*.json")) == [], "a refused challenge writes nothing"


def test_the_route_is_not_a_parameter(writing_server):
    """A caller that could set `routed_to` would be routing by the sender."""
    s, _ = writing_server
    params = {t.name: t.input_schema.get("properties", {})
              for t in asyncio.run(s.list_tools())}
    for forbidden in ("routed_to", "resolvable_by", "state", "raised_by",
                      "depth", "id", "resolved_by"):
        assert forbidden not in params["kb_challenge_raise"], forbidden
