"""Performance Agent module alias (P4 folder layout).

Re-exports the existing PerformanceAgent without changing behavior.
"""

from __future__ import annotations

from aetheros.agents.performance_agent import PerformanceAgent

__all__ = ["PerformanceAgent"]
