"""MS `.claude/agents/*.md` -- the lens definitions, into the index.

**This is the layer that makes four declaration forms comparable**, and it is
the whole of that layer: MS's five lenses become `kind=agent` rows, BD's nine
agents and rt's two personas arrive through their own adapters, and the
comparison happens in the one `Doc` shape they all land in.

It used to say *"for `map/04-agents/ms/`"*. Decision 38 retired that folder --
nothing ever generated it, and a generated rendering of an agent file would give
a caller something to cite other than the declaration itself. `kb_search`'s
`profile_candidates` cites `ms@sha:.claude/agents/<lens>.md#owns`, the owner's
own file, which is what the map layer was for.

It is also the adapter that records the fact the whole `export/` decision rests
on:

    tools: Read, Grep, Glob

Five lenses, no MCP tool declared. They cannot call Librarian, so after
migration they read a generated copy or they read nothing -- and `grep` against
a missing directory returns empty rather than failing.
"""

from __future__ import annotations

import re
from pathlib import Path

from librarian.doc import Doc
from librarian.md import frontmatter, sections

_LENS = re.compile(r"\bLens\s+(\d+)\b", re.IGNORECASE)
_GATES = re.compile(r"\bG\d+[a-z]?\b")


def ms_agents(root: Path, sha: str) -> list[Doc]:
    agents = root / ".claude" / "agents"
    if not agents.is_dir():
        raise FileNotFoundError(f"{agents} does not exist")

    out: list[Doc] = []
    for path in sorted(agents.glob("*.md")):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        fm, body = frontmatter(text)

        name = str(fm.get("name") or path.stem)
        desc = str(fm.get("description") or "")
        tools = fm.get("tools")
        tools = [t.strip() for t in tools.split(",")] if isinstance(tools, str) else (tools or [])

        lens = _LENS.search(desc)
        gates = sorted(set(_GATES.findall(desc)), key=lambda g: (int(g[1:].rstrip("abcd") or 0), g))

        # The definition itself: one row, because its frontmatter is the unit.
        out.append(Doc(
            repo="ms", path=rel, locator="definition", commit_sha=sha,
            kind="agent",
            origin=f"lens-{lens.group(1)}" if lens else None,
            # An agent definition is a declaration, not a measurement.
            provenance="declaration",
            title=f"{name}" + (f" (lens {lens.group(1)})" if lens else ""),
            body=desc,
            conditions=("tools: " + ", ".join(tools)) if tools else "tools: <inherited>",
        ))
        # Gate ownership is what a caller asks about, so it gets its own locator.
        if gates:
            out.append(Doc(
                repo="ms", path=rel, locator="gates", commit_sha=sha,
                kind="agent", origin=f"lens-{lens.group(1)}" if lens else None,
                provenance="declaration",
                title=f"{name}: gates named in its own description",
                body=" ".join(gates),
            ))
        for s in sections(body):
            out.append(Doc(
                repo="ms", path=rel, locator=s.locator, commit_sha=sha,
                kind="agent", origin=f"lens-{lens.group(1)}" if lens else None,
                provenance="declaration",
                title=f"{name} -- {s.title}" if s.title else name,
                body=s.body,
            ))
    return out
