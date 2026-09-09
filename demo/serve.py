"""Preview the always-on transport PLAN.md 3.4 describes, without changing it.

Decision 26 pins v1 to stdio, so `mcp_server/server.py` is not touched. This
launcher imports the same `build()` and runs it over streamable HTTP, with the
demo pages mounted at the SAME origin so the browser can call `/mcp` directly --
no CORS, no proxy, and nothing about the server itself is different.

    python demo/serve.py                      # http://127.0.0.1:8931/

`/log` is a **preview of `kb_feedback`, not `kb_feedback`.** That tool is one of
the two unbuilt writes, and it is unbuilt because the publish-gate scope is open
(PLAN.md 6.1, open decision (a)): a retrieval record stores raw query text and
this repository is public. So the record is written here, by the launcher, to
`kb/08-retrieval/sessions/` -- which `.gitignore` already excludes for exactly
that reason -- and no write tool is added to the server.

The record follows FEEDBACK.md 2's schema, including the parts that constrain it:

  `verdict` defaults to `not_searched`, because an unrecorded query is not "it
  was fine", it is "this was never checked" (constraint 1).

  `cited` is reported by the caller and never inferred (decision 19). A search
  writes it empty; marking a hit cited is a second, explicit call.

  There is no satisfaction score. FEEDBACK.md 4 prohibits one -- a scalar
  becomes a stored claim that this hit matters more, which is `value_score`
  returning in new dress.
"""

import json
import sys
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import uvicorn
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from mcp_server.server import build

HOST, PORT = "127.0.0.1", 8931
SESSIONS = REPO / "kb" / "08-retrieval" / "sessions"

VERDICTS = {"useful", "wrong_ranking", "missing_entry", "wrong_tier",
            "no_result", "not_searched"}


def _path(sid: str) -> Path:
    """Session files are named by their own id, and the id is validated.

    Without the character check the id is a path, and a caller could name any
    file on disk. Everything written here is derived from a browser request.
    """
    if not sid.startswith("ret-") or not sid[4:].isalnum():
        raise ValueError(f"bad session id {sid!r}")
    return SESSIONS / f"{sid}.json"


async def log_write(request: Request) -> JSONResponse:
    body = await request.json()

    sid = body.get("id")
    if sid:                                    # a second call about one query
        p = _path(sid)
        if not p.exists():
            return JSONResponse({"error": f"no session {sid}"}, status_code=404)
        rec = json.loads(p.read_text(encoding="utf-8"))
    else:
        sid = "ret-" + uuid.uuid4().hex[:8]
        rec = {
            "id": sid,
            "schema": "librarian.retrieval/0.1",
            "query": str(body.get("query") or ""),
            "caller_profile": str(body.get("caller_profile") or "neutral"),
            "asked_by": str(body.get("asked_by") or "human"),
            "index_sha": body.get("index_sha"),
            "index_stale": bool(body.get("index_stale")),
            "returned": list(body.get("returned") or []),
            "cited": [],
            "missing": [],
            "verdict": "not_searched",
            "action": "none",
            "action_ref": None,
            "note": None,
            "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    # Only the caller-reported fields are updatable, and `verdict` is checked
    # against its vocabulary rather than stored as whatever arrived.
    if "cited" in body:
        rec["cited"] = list(body["cited"] or [])
    if "verdict" in body:
        v = str(body["verdict"])
        if v not in VERDICTS:
            return JSONResponse({"error": f"verdict {v!r} not in {sorted(VERDICTS)}"},
                                status_code=400)
        rec["verdict"] = v
    if "note" in body:
        rec["note"] = body["note"] or None

    SESSIONS.mkdir(parents=True, exist_ok=True)
    _path(sid).write_text(json.dumps(rec, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    return JSONResponse(rec)


async def log_list(request: Request) -> JSONResponse:
    """Newest first. The point of the list is that it is short and readable."""
    if not SESSIONS.is_dir():
        return JSONResponse({"sessions": [], "count": 0})
    files = sorted(SESSIONS.glob("ret-*.json"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for p in files[:60]:
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return JSONResponse({"sessions": out, "count": len(files)})


server = build()

# `stateless_http` + `json_response` make every call one self-contained POST
# returning plain JSON: what a browser fetch can do without holding a session.
app = server.streamable_http_app(
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
    host=HOST,
)

app.routes.append(Route("/log", log_write, methods=["POST"]))
app.routes.append(Route("/log", log_list, methods=["GET"]))
# Mounted last, so `/mcp` and `/log` still win: Starlette matches in order.
app.routes.append(Mount("/", app=StaticFiles(directory=REPO / "demo", html=True)))

if __name__ == "__main__":
    print(f"search  http://{HOST}:{PORT}/search.html")
    print(f"console http://{HOST}:{PORT}/live.html")
    print(f"summary http://{HOST}:{PORT}/index.html")
    print(f"mcp     http://{HOST}:{PORT}/mcp")
    print(f"log     {SESSIONS}")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
