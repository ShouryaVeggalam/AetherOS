"""Policy-engine data contracts.

TelemetrySnapshot is a flat, policy-friendly view of one sample.
PolicyRecommendation is advice only — never an executable command.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from aetheros.telemetry.models import SystemSnapshot

SeverityLevel = Literal["normal", "warning", "critical"]

# Severity rank used when sorting recommendations (higher = more urgent).
SEVERITY_RANK: dict[SeverityLevel, int] = {
    "normal": 0,
    "warning": 1,
    "critical": 2,
}


@dataclass(frozen=True, slots=True)
class TelemetrySnapshot:
    """Flat telemetry input consumed by policy rules.

    Attributes:
        timestamp: When the sample was taken (UTC preferred).
        cpu_percent: Overall CPU usage 0–100.
        memory_percent: Used RAM as a percent of total.
        disk_percent: Highest disk-use percent among watched mounts.
        battery_percent: Charge percent, or None if no battery.
        process_count: Number of processes in the sample.
        top_processes: Process names ranked by CPU (highest first).
    """

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    battery_percent: float | None
    process_count: int
    top_processes: tuple[str, ...]

    @classmethod
    def from_system_snapshot(cls, snapshot: SystemSnapshot) -> TelemetrySnapshot:
        """Adapt a Phase-1 SystemSnapshot into this flat policy input.

        Args:
            snapshot: Rich telemetry sample from the collector.

        Returns:
            A TelemetrySnapshot suitable for rule evaluation.
        """

        disk_percent = max((d.percent for d in snapshot.disks), default=0.0)
        battery = snapshot.battery.percent if snapshot.battery else None
        names = tuple(proc.name for proc in snapshot.processes)
        return cls(
            timestamp=snapshot.collected_at,
            cpu_percent=snapshot.cpu.percent,
            memory_percent=snapshot.memory.percent,
            disk_percent=disk_percent,
            battery_percent=battery,
            process_count=len(snapshot.processes),
            top_processes=names,
        )


@dataclass(frozen=True, slots=True)
class PolicyRecommendation:
    """A single non-executing recommendation from the policy engine.

    Attributes:
        level: Severity — normal, warning, or critical.
        title: Short human-readable label.
        reason: Why this recommendation was produced.
        recommended_action: Suggested operator action (text only).
        confidence: How confident the rule is, from 0 to 100.
    """

    level: SeverityLevel
    title: str
    reason: str
    recommended_action: str
    confidence: int

    def __post_init__(self) -> None:
        """Validate confidence stays within 0–100."""

        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")
