"""The MCP surface. Read-only, index-only, and explicit when there is no index."""

import asyncio

import pytest

from librarian.doc import Doc
from librarian.index import build

READ_TOOLS = {"kb_search", "kb_get", "kb_neighbors", "kb_supplies", "kb_gaps",
              "kb_stale", "kb_inputs"}
WRITE_TOOLS = {"kb_feedback", "kb_challenge_raise"}
TOOLS = READ_TOOLS | WRITE_TOOLS


def _call(server, name, args=None):
    res = asyncio.run(server.call_tool(name, args or {}))
    assert res.is_error is False, f"{name} errored"
    return res.structured_content


@pytest.fixture
def server(tmp_path, monkeypatch):
    from mcp.server.mcpserver import MCPServer

    from mcp_server import tools

    docs = [
        Doc(repo="ms", path="kb/expertise/a.md", locator="verdict", commit_sha="s1",
            kind="expertise", evidence="measured", tier=1, has_falsifier=True,
            title="coverslip thickness", body="170 um in use. See [[b]]."),
        Doc(repo="ms", path="kb/expertise/b.md", locator="verdict", commit_sha="s1",
            kind="expertise", evidence="assumed", tier=3,
            title="immersion media", body="oil and water"),
        Doc(repo="ms", path="kb/expertise/a.md", locator="related", commit_sha="s1",
            kind="expertise", title="coverslip thickness -- Related", body="[[missing-entry]]"),
    ]
    from librarian.links import extract
    links = extract(docs, {"kb/expertise/a.md", "kb/expertise/b.md"},
                    {"kb/expertise/a.md": "---\nid: a\n---\n"})
    idx_path = tmp_path / "kb.sqlite"
    build(docs, idx_path, {"ms": "s1"}, links)

    s = MCPServer(name="librarian-test", version="0.0.0")
    tools.register(s, index_path=idx_path, profiles_dir=tmp_path / "profiles")
    return s


def test_the_declared_tools_are_the_registered_tools():
    from mcp_server.server import build as build_server
    s = build_server()
    assert {t.name for t in asyncio.run(s.list_tools())} == TOOLS


def test_which_tools_write_is_declared_and_not_discovered():
    """The annotation is how a client knows before calling, not after.

    Asserted as a **partition** rather than as "everything is read-only",
    which is what this said while nothing wrote. Stated that way it would have
    had to be deleted the moment a write tool landed -- and a test deleted to
    make room for a change stops guarding the thing it was for.

    It then did its job: adding `kb_challenge_raise` failed here until the tool
    was listed, which is the one place a write reaching the surface
    undeclared would have been caught.
    """
    from mcp_server.server import build as build_server
    listed = {t.name: t.annotations for t in asyncio.run(build_server().list_tools())}
    assert set(listed) == TOOLS

    writers = {n for n, a in listed.items() if a.read_only_hint is not True}
    assert writers == WRITE_TOOLS, writers

    for name, a in listed.items():
        assert a is not None, name
        # Nothing here is destructive, writers included: a write is an
        # append-only record under a content-addressed name, so a retry
        # collapses into the record it already wrote (PLAN.md §3.7).
        assert a.destructive_hint is False, name
    for name in WRITE_TOOLS:
        assert listed[name].idempotent_hint is True, name


def test_a_missing_index_is_a_status_not_a_crash(tmp_path):
    """The server is launched by a client that cannot see the build step."""
    from mcp.server.mcpserver import MCPServer

    from mcp_server import tools
    s = MCPServer(name="t", version="0")
    tools.register(s, index_path=tmp_path / "absent.sqlite",
                   profiles_dir=tmp_path / "profiles",
                   # Given a real directory on purpose: without one
                   # `kb_feedback` answers `no_session_store` and never reaches
                   # the index, which would make it pass this test vacuously.
                   sessions_dir=tmp_path / "sessions",
                   challenge_dir=tmp_path / "challenge")
    for name in sorted(TOOLS - {"kb_inputs"}):   # kb_inputs reports a missing
        # checkout before it reaches the index, so it has its own case below
        args = {"question": "x"} if name == "kb_search" else {}
        if name in {"kb_get", "kb_neighbors"}:
            args = {"uid": "ms:x#y"}
        if name == "kb_supplies":
            args = {"name": "G10"}
        if name == "kb_inputs":
            args = {"computation": "radial_stiffness_n_per_m"}
        if name == "kb_feedback":
            args = {"query": "x", "caller_profile": "neutral",
                    "verdict": "no_result"}
        if name == "kb_challenge_raise":
            args = {"target_uid": "ms:kb/expertise/a.md#verdict",
                    "doubt_kind": "scope_exceeded",
                    "falsifier_cited": "ms:kb/expertise/a.md#falsification"}
        out = _call(s, name, args)
        assert out["status"] == "no_index", name
        assert "reindex" in out["detail"]
    # And nothing was written while there was no index to record against.
    assert not (tmp_path / "sessions").exists()
    assert not (tmp_path / "challenge").exists()


def test_kb_search_reports_an_unknown_profile_rather_than_guessing(server):
    out = _call(server, "kb_search", {"question": "coverslip", "caller_profile": "ms:nope"})
    assert out["status"] == "unknown_profile"
    assert out["asked_for"] == "ms:nope" and "neutral" in out["known"]


def test_kb_search_carries_coordinates_tier_and_the_notes(server):
    out = _call(server, "kb_search", {"question": "coverslip thickness"})
    assert out["status"] == "ok" and out["hits"]
    for h in out["hits"]:
        assert h["uid"].count(":") >= 1 and "#" in h["uid"]
        assert "evidence" in h and "advances" in h
        assert h["advances"] is (h["evidence"] == "measured")
    joined = " ".join(out["notes"])
    assert "searched_empty" in joined and "advances" in joined


def test_searched_empty_is_a_status(server):
    out = _call(server, "kb_search", {"question": "zzzqqqxyzzy"})
    assert out["status"] == "searched_empty" and out["hits"] == []


def test_kb_get_offers_the_sections_of_a_path_when_the_locator_misses(server):
    ok = _call(server, "kb_get", {"uid": "ms:kb/expertise/a.md#verdict"})
    assert ok["status"] == "ok" and ok["advances"] is True

    miss = _call(server, "kb_get", {"uid": "ms:kb/expertise/a.md#renamed-heading"})
    assert miss["status"] == "not_found"
    assert "ms:kb/expertise/a.md#verdict" in miss["near"]


def test_kb_neighbors_resolves_and_reports_the_unresolved(server):
    out = _call(server, "kb_neighbors", {"uid": "ms:kb/expertise/a.md#verdict"})
    assert out["status"] == "ok"
    assert [n["uid"] for n in out["neighbors"]] == ["ms:kb/expertise/b.md#verdict"]

    inbound = _call(server, "kb_neighbors",
                    {"uid": "ms:kb/expertise/b.md#verdict", "direction": "in"})
    assert [n["uid"] for n in inbound["neighbors"]] == ["ms:kb/expertise/a.md#verdict"]

    same = _call(server, "kb_neighbors",
                 {"uid": "ms:kb/expertise/a.md#verdict", "relation": "same_file"})
    assert [n["uid"] for n in same["neighbors"]] == ["ms:kb/expertise/a.md#related"]

    bad = _call(server, "kb_neighbors",
                {"uid": "ms:kb/expertise/a.md#verdict", "direction": "sideways"})
    assert bad["status"] == "bad_request"


def test_kb_stale_answers_two_different_questions(server):
    out = _call(server, "kb_stale")
    assert out["status"] == "ok"
    assert out["indexed_at"] == {"ms": "s1"}
    assert out["index_stale"] is False          # no cache dir, so nothing to compare
    assert out["links"]["missing"] == 1          # the [[missing-entry]] wikilink
    assert "review_expired" in out["entry_defects"]
    # The falsifier check is not duplicated here: drift.py owns it, with the
    # majority rule that keeps it from reporting calibrations.
    assert "no_falsifier" not in out["entry_defects"]


# --- profile candidates (PLAN.md 5.3) ---------------------------------------

def test_the_candidate_field_is_always_present_and_always_unapplied(server):
    """Absent, the field would be indistinguishable from *"no candidate"*.

    That is constraint ① in miniature: this surface answers with a state, not
    with silence. `candidates_applied` is asserted on every path because it is
    the promise the caller is being asked to rely on -- the hits were ranked by
    the profile they declared, and nothing below re-ranked them.
    """
    for args in ({"question": "coverslip thickness"},
                 {"question": "coverslip", "caller_profile": "ms:nope"}):
        out = _call(server, "kb_search", args)
        assert "profile_candidates" in out, args
        assert out["candidates_applied"] is False, args


def _server_with_profile(tmp_path):
    """One lens profile and the agent file that declares it -- both ends."""
    from mcp.server.mcpserver import MCPServer

    from mcp_server import tools

    docs = [
        Doc(repo="ms", path=".claude/agents/sample-optics.md", locator="owns",
            commit_sha="s1", kind="agent", origin="lens-4",
            provenance="declaration", title="sample-optics: owns",
            body="Objective choice, immersion, coverslip thickness, chamber."),
        Doc(repo="ms", path="kb/expertise/a.md", locator="verdict",
            commit_sha="s1", kind="expertise", evidence="measured", tier=1,
            title="coverslip thickness", body="170 um in use."),
    ]
    idx_path = tmp_path / "kb.sqlite"
    build(docs, idx_path, {"ms": "s1"})

    pdir = tmp_path / "profiles"
    pdir.mkdir()
    (pdir / "ms-lens4.yaml").write_text(
        "id: ms:lens-4-sample-optics\nlens: 4\n", encoding="utf-8")

    s = MCPServer(name="librarian-test", version="0.0.0")
    tools.register(s, index_path=idx_path, profiles_dir=pdir)
    return s


def test_a_candidate_reaches_the_caller_with_its_citation(tmp_path):
    """End to end: the question's word, the profile, and the file that says so."""
    s = _server_with_profile(tmp_path)
    out = _call(s, "kb_search", {"question": "which immersion and coverslip"})
    cands = out["profile_candidates"]
    assert cands, "the lens declares both words; it should be a candidate"
    c = cands[0]
    assert c["profile"] == "ms:lens-4-sample-optics"
    assert c["because"] == "ms:.claude/agents/sample-optics.md#owns"
    assert set(c["matched_terms"]) <= {"immersion", "coverslip"}
    assert out["candidates_applied"] is False


def test_the_unknown_profile_branch_gives_a_reason_not_a_menu(tmp_path):
    """The branch §5.3 was written about.

    It returned the known ids and nothing to choose by, which left the caller
    needing to know the corpus before it could query the corpus. It still
    refuses to guess -- the status is unchanged and no search was run under an
    assumed profile -- but the refusal now carries a cited suggestion.
    """
    s = _server_with_profile(tmp_path)
    out = _call(s, "kb_search",
                {"question": "which immersion and coverslip",
                 "caller_profile": "ms:lens-4"})
    assert out["status"] == "unknown_profile"
    assert "hits" not in out, "a rejected profile must not be searched under"
    assert out["profile_candidates"][0]["profile"] == "ms:lens-4-sample-optics"
    assert out["profile_candidates"][0]["because"].startswith("ms:.claude/agents/")
