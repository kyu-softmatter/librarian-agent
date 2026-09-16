"""The MCP server: assemble the tools, run over stdio.

    python -m mcp_server.server

Launched by an MCP client, normally through `.mcp.json` in the repository root.

**Seven read tools and one write.** `kb_feedback` appends a retrieval session to
`kb/08-retrieval/sessions/`, which is local and permanently gitignored -- the
publish-gate scope that blocked it is settled (PLAN.md §6.1, decision 37).
Nothing in any source repository is written, ever.

Still absent: `kb_challenge_raise`. It has to route by the type of the
falsifier it cites, and that routing is the retirement mechanism rather than a
write path.
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.mcpserver import MCPServer

from . import tools

ROOT = Path(__file__).resolve().parent.parent
NAME = "librarian"

INSTRUCTIONS = """\
One indexed knowledge base over the microscope repository, with retrieval
profiled per calling agent. Seven tools read; `kb_feedback` writes one local,
uncommitted record. **Nothing here writes to any source repository, ever** --
anything that has to land there arrives as a pull request.

Four things about the results, each of which looks like a failure and is not.

`status: searched_empty` means the corpus was searched and held nothing. It is
distinct from `not_searched`, which is the absence of a record that anyone
looked. Report the first; do not treat it as a broken tool.

`index_stale: true` means a repository has moved since the index was built, so
the answer may be behind. Run `librarian reindex` or say so; the answer itself
is still valid.

`advances: false` on a hit means that evidence tier cannot advance a verdict. A
literature value never can, by rule -- it lets a gate compute instead of
refusing, and claims no measurement. Report the tier rather than working around
it.

`status: blocked` from `kb_supplies`, and a `filled: 0` row from `kb_gaps`, mean
no entry supplies that field anywhere. The microscope returns BLOCKED by design
when an input is missing, so the useful answer is which input.

Two habits worth keeping.

Cite `repo@sha:path#locator`, which every hit carries, not the snippet. A claim
that cannot be walked back to a location is not usable here.

`caller_profile` changes what is returned, deliberately. The same question under
`ms:lens-5-photo-perturbation` and `ms:lens-4-sample-optics` lands in different
evidence, because the two lenses own different things. Use `neutral` when no
lens applies rather than guessing at one.

One thing worth doing rather than knowing. **Report which hits you actually
cited, with `kb_feedback`.** Retrieval here has no grader, so a past confirmed
citation stands in for one, and `cited` is the only signal that improves it. It
is never inferred from what you were sent: inferred, it stops being a fact.
Recording nothing leaves the query at `not_searched`, which means *this was
never checked* rather than *it was fine*.

This server originates no numbers. Every value it returns is quoted from a file
with its location attached.
"""


def build() -> MCPServer:
    """The server, tools registered. Opens no file."""
    server = MCPServer(name=NAME, instructions=INSTRUCTIONS, version="0.1.0")
    tools.register(
        server,
        index_path=ROOT / "index" / "kb.sqlite",
        profiles_dir=ROOT / "profiles",
        cache_dir=ROOT / "cache",
        sessions_dir=ROOT / "kb" / "08-retrieval" / "sessions",
    )
    return server


def main() -> None:
    build().run(transport="stdio")


if __name__ == "__main__":
    main()
