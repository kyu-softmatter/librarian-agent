"""One parser per repository contract.

Parse the declared contract; do not hard-code paths. Each adapter asserts a
non-zero document count for its source -- see ./README.md for why that assertion
is the point rather than a habit.

**A source name is prefixed with the repo it parses**, and `librarian.scan`
selects on that prefix. Without the convention a scan of one checkout would run
every adapter against it and report `source_empty` at error severity for the
ones that do not apply -- turning the check that catches a silently empty read
into the thing that fires on every run.
"""

from .ms_kb import ms_kb
from .ms_data import ms_data
from .ms_docs import ms_docs
from .ms_agents import ms_agents
from .bd_wiki import bd_wiki
from .bd_source import bd_source
from .bd_entries import bd_entries

ADAPTERS = {
    "ms_kb": ms_kb,
    "ms_data": ms_data,
    "ms_docs": ms_docs,
    "ms_agents": ms_agents,
    "bd_wiki": bd_wiki,
    "bd_source": bd_source,
    "bd_entries": bd_entries,
}

__all__ = [
    "ADAPTERS",
    "ms_kb", "ms_data", "ms_docs", "ms_agents",
    "bd_wiki", "bd_source", "bd_entries",
]
