"""Heartbeat producer — local read-only resource pulses for federation.

Configurable interval. Never sends commands. Never mutates remote state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from aetheros.federation.models import PROTOCOL_VERSION, Heartbeat, NodeIdentity
from aetheros.federation.protocol import ProtocolMessage
from aetheros.federation.serializer import encode_heartbeat


class TelemetryLike(Protocol):
    """Minimal telemetry surface used to build heartbeats."""

    cpu_percent: float
    memory_percent: float
    disk_percent: float
    battery_percent: float | None


DEFAULT_HEARTBEAT_INTERVAL_SEC = 5.0


@dataclass(frozen=True, slots=True)
class HeartbeatConfig:
    """Local heartbeat schedule (seconds)."""

    interval_sec: float = DEFAULT_HEARTBEAT_INTERVAL_SEC

    def __post_init__(self) -> None:
        if self.interval_sec <= 0:
            raise ValueError("interval_sec must be > 0")


def build_heartbeat(
    node: NodeIdentity,
    telemetry: TelemetryLike,
    *,
    network: float = 0.0,
    now: datetime | None = None,
) -> Heartbeat:
    """Build an immutable heartbeat from local telemetry."""

    stamp = now or datetime.now(UTC)
    battery = telemetry.battery_percent
    return Heartbeat(
        node_id=node.node_id,
        cpu=float(telemetry.cpu_percent),
        memory=float(telemetry.memory_percent),
        disk=float(telemetry.disk_percent),
        network=max(0.0, min(100.0, float(network))),
        battery=None if battery is None else float(battery),
        timestamp=stamp,
        protocol_version=PROTOCOL_VERSION,
    )


def heartbeat_message(
    node: NodeIdentity,
    heartbeat: Heartbeat,
    *,
    now: datetime | None = None,
) -> ProtocolMessage:
    """Wrap a heartbeat in a versioned protocol envelope."""

    stamp = now or heartbeat.timestamp
    return ProtocolMessage(
        kind="heartbeat",
        protocol_version=PROTOCOL_VERSION,
        payload=encode_heartbeat(heartbeat),
        sent_at=stamp,
        source_node_id=node.node_id,
    )


def should_emit(
    *,
    last_emitted: datetime | None,
    now: datetime,
    config: HeartbeatConfig | None = None,
) -> bool:
    """Return True when enough time has elapsed since the last heartbeat."""

    cfg = config or HeartbeatConfig()
    if last_emitted is None:
        return True
    elapsed = (now - last_emitted).total_seconds()
    return elapsed >= cfg.interval_sec
