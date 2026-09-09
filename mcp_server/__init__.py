"""The MCP surface over the index.

    python -m mcp_server.server

Seven read tools. Nothing here writes, and nothing here reads a source repository:
every answer comes from `index/kb.sqlite`, so the server has one dependency and
a stale index reports itself rather than being silently different from the repos.
"""
