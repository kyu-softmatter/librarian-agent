"""One parser per repository contract.

Parse the declared contract; do not hard-code paths. Each adapter asserts a
non-zero document count for its source -- see ./README.md for why that assertion
is the point rather than a habit.
"""

from .ms_kb import ms_kb
from .ms_data import ms_data
from .ms_docs import ms_docs
from .ms_agents import ms_agents

ADAPTERS = {
    "ms_kb": ms_kb,
    "ms_data": ms_data,
    "ms_docs": ms_docs,
    "ms_agents": ms_agents,
}

__all__ = ["ADAPTERS", "ms_kb", "ms_data", "ms_docs", "ms_agents"]
