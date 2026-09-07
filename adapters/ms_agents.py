"""MS `.claude/agents/*.md` -- the lens definitions, for `map/04-agents/ms/`.

This is the only adapter whose output is **derived**: agent definitions change
with every commit, so what it produces is regenerated in full and never
hand-edited (`TREE.md` 2-A). It is also the adapter that records the fact the
whole `export/` decision rests on:

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
