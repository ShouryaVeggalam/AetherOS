"""Runtime package — agentic deliberation entry points.

Distinct from ``aetheros.core`` (plugin host). This package owns the
multi-agent collaboration loop. Report types are owned by ``agents``.
"""

from aetheros.agents.report import AgenticReport, AgentStatusRow
from aetheros.runtime.agentic import AgenticRuntime

__all__ = [
    "AgentStatusRow",
    "AgenticReport",
    "AgenticRuntime",
]
