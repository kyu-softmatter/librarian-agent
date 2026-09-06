# `export/` — derived, outbound

Read-only copies that Librarian generates **back into the source repositories.**

```
ms/    what MS's five lenses reach with Read/Grep/Glob
bd/    what BD reads offline                              [v2]
```

## Why this exists

MS's five lens subagents declare `tools: Read, Grep, Glob` and **no MCP tool.**
They cannot call Librarian. After migration, without this folder they would read
nothing — and `grep` against a missing directory returns empty, not an error, so
a lens would return a verdict with zero knowledge and no sign that anything was
wrong.

The alternative was rewriting 5 lens definitions plus 9 BD agents to add MCP
tools, which makes knowledge availability depend on a running service. Rejected
because **the default is failure**: a design that silently reports zero uses that
principle backwards.

## Invariant

The canonical copy lives in `../kb/`. What lands in a source repository is a
derived artefact **that nobody may hand-edit**. So "delete the KB" becomes
precisely "delete the KB along with the authority to edit it."

Wiring (git subtree vs generated commit) is decided at MIGRATION Step 3.
