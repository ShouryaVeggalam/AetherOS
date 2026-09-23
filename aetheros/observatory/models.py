"""Observatory data contracts for AetherOS v1.1.

Immutable telemetry points and system events. Never mutate the OS.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

GraphMetric = Literal["cpu", "memory", "disk"]
EventType = Literal[
    "cpu_spike",
    "memory_pressure",
    "intent_changed",
    "research_completed",
    "safety_blocked",
]
Severity = Literal["info", "warning", "critical"]


@dataclass(frozen=True, slots=True)
class TelemetryPoint:
    """One immutable telemetry sample stored by the observatory.

    Attributes:
        timestamp: Sample time (UTC preferred).
        cpu: CPU percent 0–100.
        memory: Memory percent 0–100.
        disk: Disk percent 0–100.
        battery: Battery percent, or None if unavailable.
        intent: Active intent profile name.
    """

    timestamp: datetime
    cpu: float
    memory: float
    disk: float
    battery: float | None
    intent: str


@dataclass(frozen=True, slots=True)
class SystemEvent:
    """One observatory timeline event derived from history or pipeline.

    Attributes:
        timestamp: When the event was detected.
        type: Event category key.
        severity: info, warning, or critical.
        title: Short timeline label.
        description: Human-readable detail grounded in data.
    """

    timestamp: datetime
    type: EventType
    severity: Severity
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class TimelineWindow:
    """Named history windows for graphs and analysis.

    Attributes:
        last_60_seconds: Points from the last minute.
        last_5_minutes: Points from the last five minutes.
        last_hour: Points from the last hour.
    """

    last_60_seconds: tuple[TelemetryPoint, ...]
    last_5_minutes: tuple[TelemetryPoint, ...]
    last_hour: tuple[TelemetryPoint, ...]
