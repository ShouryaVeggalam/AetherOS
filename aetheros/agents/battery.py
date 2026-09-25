"""Battery Agent module alias (P4 folder layout).

Re-exports the existing BatteryAgent without changing behavior.
"""

from __future__ import annotations

from aetheros.agents.battery_agent import BatteryAgent

__all__ = ["BatteryAgent"]
