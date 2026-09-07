"""The MCP surface. Read-only, index-only, and explicit when there is no index."""

import asyncio

import pytest

from librarian.doc import Doc
from librarian.index import build

TOOLS = {"kb_search", "kb_get", "kb_neighbors", "kb_supplies", "kb_gaps", "kb_stale"}


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


def test_every_tool_is_annotated_read_only():
    """Nothing here writes. The annotation is how a client knows before calling."""
    from mcp_server.server import build as build_server
    for t in asyncio.run(build_server().list_tools()):
        assert t.annotations is not None, t.name
        assert t.annotations.read_only_hint is True, t.name
        assert t.annotations.destructive_hint is False, t.name


def test_a_missing_index_is_a_status_not_a_crash(tmp_path):
    """The server is launched by a client that cannot see the build step."""
    from mcp.server.mcpserver import MCPServer

    from mcp_server import tools
    s = MCPServer(name="t", version="0")
    tools.register(s, index_path=tmp_path / "absent.sqlite",
                   profiles_dir=tmp_path / "profiles")
    for name in TOOLS:
        args = {"question": "x"} if name == "kb_search" else {}
        if name in {"kb_get", "kb_neighbors"}:
            args = {"uid": "ms:x#y"}
        if name == "kb_supplies":
            args = {"name": "G10"}
        out = _call(s, name, args)
        assert out["status"] == "no_index", name
        assert "reindex" in out["detail"]


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
