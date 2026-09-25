"""Telemetry Agent module alias (P4 folder layout).

Re-exports the existing TelemetryAgent without changing behavior.
"""

from __future__ import annotations

from aetheros.agents.telemetry_agent import TelemetryAgent

__all__ = ["TelemetryAgent"]
