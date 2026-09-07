"""The MCP server: assemble the tools, run over stdio.

    python -m mcp_server.server

Launched by an MCP client, normally through `.mcp.json` in the repository root.

Deliberately absent: anything that writes. `kb_challenge_raise` and `kb_feedback`
are the write half of this surface and they are not here yet -- a challenge has
to route by falsifier type, and a retrieval record stores raw query text in a
public repository, so the publish-gate scope has to be settled first.
"""

from __future__ import annotations

from pathlib import Path

from mcp.server.mcpserver import MCPServer

from . import tools

ROOT = Path(__file__).resolve().parent.parent
NAME = "librarian"

INSTRUCTIONS = """\
One indexed knowledge base over the microscope repository, with retrieval
profiled per calling agent. Read-only: nothing here writes to any repository.

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

This server originates no numbers. Every value it returns is quoted from a file
with its location attached.
"""


def build() -> MCPServer:
    """The server, with the read tools registered. Opens no file."""
    server = MCPServer(name=NAME, instructions=INSTRUCTIONS, version="0.1.0")
    tools.register(
        server,
        index_path=ROOT / "index" / "kb.sqlite",
        profiles_dir=ROOT / "profiles",
        cache_dir=ROOT / "cache",
    )
    return server


def main() -> None:
    build().run(transport="stdio")


if __name__ == "__main__":
    main()
