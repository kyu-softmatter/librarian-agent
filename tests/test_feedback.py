"""`kb_feedback`: what it records, and the six things it refuses.

FEEDBACK.md's rules are mostly prohibitions, and a prohibition stated in prose
and unenforced is how `kb/08-retrieval/` would become the one folder here that
violates *prose is not state*. Each refusal below is one of those rules made
executable, so the test file and the design document are the same list.
"""

import asyncio
import json
import pathlib

import pytest

from librarian.doc import Doc
from librarian.feedback import (FeedbackError, NOT_A_VERDICT, VERDICTS,
                                promotion_status, session, write)
from librarian.index import build

UID = "ms:data/fluorophores.yaml#AlexaFluor488"
OTHER = "ms:kb/expertise/a.md#verdict"
SHA = {"ms": "9f971a8"}
DATE = "2026-09-15"


def _session(**kw):
    base = dict(query="bleach photons for AlexaFluor488 at 470 nm",
                caller_profile="ms:lens-5-photo-perturbation",
                verdict="useful", returned=[UID, OTHER], cited=[UID],
                index_sha=SHA, index_stale=False)
    return session(**{**base, **kw})


# --- what it records --------------------------------------------------------

def test_a_session_records_the_fact_and_not_a_judgment():
    """*"which hits were cited"* is a fact; *"it was good"* is not. And there is
    no place to put the second -- no score field exists to be averaged."""
    rec = _session()
    assert rec["cited"] == [UID] and rec["verdict"] == "useful"
    assert rec["index_sha"] == SHA and rec["index_stale"] is False
    assert not [k for k in rec if "score" in k or "satisfaction" in k]
    assert "note" not in rec, "an absent note is absent, not null"


def test_a_note_is_carried_but_nothing_branches_on_its_content():
    """FEEDBACK §4②: *"is there code that reads this field and branches?"*

    **Checked on content, not on presence**, and the first version of this test
    got that wrong: it forbade `note` from appearing at all, which flagged
    `rec["note"] = note` -- the line that stores it. Storing is not reading, and
    deciding whether to serialize a key is not treating prose as state.

    So what is forbidden is a `note` read inside a comparison or a method call:
    `== `, `in`, `startswith`. Truthiness is allowed and is the one use.
    """
    import ast

    import librarian.feedback as fb

    rec = _session(note="the registry field is empty so the gate is still BLOCKED")
    assert rec["note"].startswith("the registry field")

    tree = ast.parse(pathlib.Path(fb.__file__).read_text(encoding="utf-8"))

    def mentions_note(node) -> bool:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and sub.id == "note":
                return True
            if isinstance(sub, ast.Constant) and sub.value == "note":
                return True
        return False

    offenders = [ast.dump(n)[:90] for n in ast.walk(tree)
                 if isinstance(n, (ast.Compare, ast.Call)) and mentions_note(n)]
    assert offenders == [], offenders


def test_the_verdict_vocabulary_separates_causes():
    """A scalar renders 20 ranking failures and 20 missing entries as one
    number, while their fixes live in `profiles/` and `kb/` respectively."""
    assert set(VERDICTS) == {"useful", "wrong_ranking", "missing_entry",
                             "wrong_tier", "no_result"}
    assert "profiles/" in VERDICTS["wrong_ranking"]
    assert "kb/" in VERDICTS["missing_entry"]


# --- what it refuses --------------------------------------------------------

def test_not_searched_cannot_be_recorded():
    """The sharpest of the refusals, and it is a reading of decision 2.

    `not_searched` is the **default of a query nobody recorded** -- "this was
    never checked", which is constraint ①. Calling this tool is itself the
    record that someone looked, so accepting it would let a caller file the
    absence of a record as a record and collapse the one distinction
    BUILD.md §1's four-identical-faces problem turns on.
    """
    with pytest.raises(FeedbackError, match="never checked"):
        _session(verdict=NOT_A_VERDICT)
    assert NOT_A_VERDICT not in VERDICTS


def test_useful_with_nothing_cited_is_refused():
    """§5: a session with no citation carries no signal, and `useful` means the
    cited hit was near the top. Accepted, it would be a promotable record
    asserting a citation it does not have."""
    with pytest.raises(FeedbackError, match="no signal"):
        _session(cited=[])


def test_citing_something_that_was_not_returned_is_refused():
    with pytest.raises(FeedbackError, match="not in `returned`"):
        _session(cited=["ms:kb/expertise/never-sent.md#verdict"])


def test_a_name_in_asked_by_is_refused_here_and_not_only_at_the_gate():
    """`librarian.publish.gate` short-circuits on a local-only folder -- a
    session is never committed, so the gate has nothing to say about it. If the
    rule were only there, a session could carry a name and someone would have
    to strip it at promotion, by hand, having already written it down."""
    from librarian.publish import gate, is_local_only
    assert is_local_only("kb/08-retrieval/sessions/x.json")
    assert gate("kb/08-retrieval/sessions/x.json", {"asked_by": "KH"}) == []

    with pytest.raises(FeedbackError, match="not a role"):
        _session(asked_by="KH")
    for role in ("agent", "human:instrument-operator"):
        assert _session(asked_by=role)["asked_by"] == role


def test_an_unknown_profile_is_refused():
    with pytest.raises(FeedbackError, match="not a stored profile"):
        _session(known_profiles={"neutral"})


def test_a_returned_uid_absent_from_the_index_is_refused(tmp_path):
    """Refused now rather than at promotion: an oracle built on a uid the index
    does not hold could never pass, and the failure would read as a retrieval
    regression years after the typo."""
    with pytest.raises(FeedbackError, match="not in the index"):
        _session(known_uids={OTHER})
    assert _session(known_uids={UID, OTHER})["returned"] == [UID, OTHER]


def test_a_malformed_uid_is_refused():
    with pytest.raises(FeedbackError, match="not a uid"):
        _session(returned=["fluorophores.yaml"], cited=[])


def test_no_result_with_hits_is_refused():
    with pytest.raises(FeedbackError, match="not empty"):
        _session(verdict="no_result")


def test_an_empty_query_is_refused():
    with pytest.raises(FeedbackError, match="reproduction input"):
        _session(query="   ")


# --- promotion ---------------------------------------------------------------

def test_promotion_needs_two_index_states_and_promotes_nothing(tmp_path):
    """The loop this damps: what ranks high gets cited, having been cited it
    becomes an oracle, being an oracle keeps it ranked high (`C-001`)."""
    q, prof = "bleach photons", "ms:lens-5-photo-perturbation"
    kw = dict(query=q, caller_profile=prof, verdict="useful",
              returned=[UID], cited=[UID], index_stale=False)

    assert promotion_status(tmp_path, q, prof)["sessions"] == 0

    write(tmp_path, session(**kw, index_sha={"ms": "aaa1111"}), DATE)
    one = promotion_status(tmp_path, q, prof)
    assert one["qualifying_index_states"] == 1
    assert any("second, distinct index_sha" in a for a in one["awaiting"])

    write(tmp_path, session(**kw, index_sha={"ms": "bbb2222"}), DATE)
    two = promotion_status(tmp_path, q, prof)
    assert two["sessions"] == 2 and two["qualifying_index_states"] == 2
    assert not any("index_sha" in a for a in two["awaiting"])

    # The condition that never clears by itself.
    assert two["promoted"] is False
    assert any("human approval" in a for a in two["awaiting"])
    assert not list(tmp_path.glob("../oracles/*"))


def test_a_failure_record_never_counts_toward_promotion(tmp_path):
    """*"A failure record is not an oracle"* -- and it is still worth storing,
    because `wrong_ranking` is what says the fix belongs in `profiles/`."""
    q, prof = "coverslip thickness", "ms:lens-4-sample-optics"
    for sha in ("aaa1111", "bbb2222"):
        write(tmp_path, session(query=q, caller_profile=prof,
                                verdict="wrong_ranking", returned=[UID],
                                cited=[UID], index_sha={"ms": sha},
                                index_stale=False), DATE)
    out = promotion_status(tmp_path, q, prof)
    assert out["sessions"] == 2 and out["qualifying_index_states"] == 0
    assert any("verdict `useful`" in a for a in out["awaiting"])


def test_the_same_report_twice_is_one_session(tmp_path):
    rec = _session()
    a = write(tmp_path, rec, DATE)
    b = write(tmp_path, rec, DATE)
    assert a.created and not b.created and a.path == b.path
    assert len(list(tmp_path.glob("*.json"))) == 1


# --- through the MCP surface ------------------------------------------------

@pytest.fixture
def writing_server(tmp_path):
    from mcp.server.mcpserver import MCPServer

    from mcp_server import tools
    docs = [
        Doc(repo="ms", path="data/fluorophores.yaml", locator="AlexaFluor488",
            commit_sha="s1", kind="registry", title="AlexaFluor488"),
        Doc(repo="ms", path="kb/expertise/a.md", locator="verdict",
            commit_sha="s1", kind="expertise", title="coverslip thickness"),
    ]
    idx = tmp_path / "kb.sqlite"
    build(docs, idx, {"ms": "s1"})
    pdir = tmp_path / "profiles"
    pdir.mkdir()
    (pdir / "lens5.yaml").write_text(
        "id: ms:lens-5-photo-perturbation\nlens: 5\n", encoding="utf-8")
    sdir = tmp_path / "sessions"
    s = MCPServer(name="t", version="0")
    tools.register(s, index_path=idx, profiles_dir=pdir, sessions_dir=sdir)
    return s, sdir


def _call(server, name, args):
    res = asyncio.run(server.call_tool(name, args))
    assert res.is_error is False, f"{name} errored"
    return res.structured_content


def test_the_tool_writes_one_local_uncommitted_record(writing_server):
    s, sdir = writing_server
    out = _call(s, "kb_feedback", {
        "query": "bleach photons", "caller_profile": "ms:lens-5-photo-perturbation",
        "verdict": "useful", "returned": [UID], "cited": [UID]})
    assert out["status"] == "ok" and out["created"] is True
    assert out["id"].startswith("ret-")
    assert out["committed"] is False
    assert out["index_sha"] == {"ms": "s1"}
    assert out["promotion_status"]["promoted"] is False

    files = list(sdir.glob("*.json"))
    assert len(files) == 1
    rec = json.loads(files[0].read_text(encoding="utf-8"))
    assert rec["cited"] == [UID]
    assert "id" not in rec, "identity is the filename's digest, not a stored copy"


def test_a_refusal_names_the_rule_rather_than_the_field(writing_server):
    """The caller is a model. *"invalid verdict"* gets retried with another
    guess; the rule gets reported or obeyed."""
    s, sdir = writing_server
    out = _call(s, "kb_feedback", {
        "query": "bleach photons", "caller_profile": "ms:lens-5-photo-perturbation",
        "verdict": "not_searched"})
    assert out["status"] == "refused"
    assert "never checked" in out["detail"]
    assert "not_searched" in out["verdicts"]
    assert list(sdir.glob("*.json")) == [], "a refused report writes nothing"


def test_the_index_state_is_read_and_never_accepted(writing_server):
    """A caller-supplied `index_sha` could name a state that never existed, and
    promotion turns on two **distinct** SHAs. So it is not a parameter."""
    s, _ = writing_server
    schema = asyncio.run(s.list_tools())
    params = {t.name: t.input_schema.get("properties", {}) for t in schema}
    assert "index_sha" not in params["kb_feedback"]
    assert "index_stale" not in params["kb_feedback"]
    assert "id" not in params["kb_feedback"]
