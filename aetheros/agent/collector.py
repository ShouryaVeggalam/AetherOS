"""Lightweight Aether Agent telemetry collector.

Read-only userspace metrics for publishing to the cluster bus.
Never executes remote commands or modifies kernel state.
"""

from __future__ import annotations

import platform
import socket
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

import psutil

from aetheros.policy_engine.models import TelemetrySnapshot


@dataclass(frozen=True, slots=True)
class AgentSnapshot:
    """One immutable agent telemetry sample for cluster publish.

    Attributes:
        node_id: Stable agent identity.
        hostname: Local hostname.
        platform: OS platform string.
        cpu: CPU percent 0–100.
        memory: Memory percent 0–100.
        disk: Disk percent 0–100.
        battery: Battery percent, or None.
        collected_at: UTC collection time.
    """

    node_id: str
    hostname: str
    platform: str
    cpu: float
    memory: float
    disk: float
    battery: float | None
    collected_at: datetime


@dataclass
class AgentCollector:
    """Collect local read-only telemetry for the Aether Agent.

    Args:
        node_id: Stable id (generated once if omitted).
        hostname: Override hostname (defaults to socket.gethostname).
    """

    node_id: str | None = None
    hostname: str | None = None

    def __post_init__(self) -> None:
        """Resolve identity defaults."""

        if not self.node_id:
            host = self.hostname or socket.gethostname()
            self.node_id = f"local-{host}"
        if not self.hostname:
            self.hostname = socket.gethostname()

    def collect(self) -> AgentSnapshot:
        """Take one local read-only telemetry sample via psutil."""

        cpu = float(psutil.cpu_percent(interval=None))
        memory = float(psutil.virtual_memory().percent)
        try:
            disk = float(psutil.disk_usage("/").percent)
        except (OSError, PermissionError):
            disk = 0.0
        battery = _battery_percent()
        return AgentSnapshot(
            node_id=str(self.node_id),
            hostname=str(self.hostname),
            platform=platform.system() or "unknown",
            cpu=cpu,
            memory=memory,
            disk=disk,
            battery=battery,
            collected_at=datetime.now(UTC),
        )

    def from_telemetry(
        self,
        snapshot: TelemetrySnapshot,
        *,
        latency_ms: float = 0.0,
    ) -> AgentSnapshot:
        """Adapt an existing TelemetrySnapshot (avoids a second OS read)."""

        _ = latency_ms  # reserved for publisher latency tagging
        return AgentSnapshot(
            node_id=str(self.node_id),
            hostname=str(self.hostname),
            platform=platform.system() or "unknown",
            cpu=snapshot.cpu_percent,
            memory=snapshot.memory_percent,
            disk=snapshot.disk_percent,
            battery=snapshot.battery_percent,
            collected_at=snapshot.timestamp,
        )


def stable_node_id(prefix: str, hostname: str) -> str:
    """Build a deterministic node id from prefix + hostname."""

    digest = uuid.uuid5(uuid.NAMESPACE_DNS, f"{prefix}:{hostname}").hex[:12]
    return f"{prefix}-{digest}"


def _battery_percent() -> float | None:
    """Read battery percent when available."""

    try:
        batt = psutil.sensors_battery()
    except (AttributeError, OSError, PermissionError):
        return None
    if batt is None:
        return None
    return float(batt.percent)
