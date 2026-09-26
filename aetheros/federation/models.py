"""Federation Protocol models — immutable, read-only node contracts.

v4.0 P1. Nodes exchange snapshots and heartbeats only. Never represents
remote execution, SSH, or mutable shared state. No private user data.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal

PROTOCOL_VERSION = "1.0.0"

NodeStatus = Literal["online", "offline", "unknown"]


@dataclass(frozen=True, slots=True)
class NodeIdentity:
    """Stable identity of one AetherOS federation node."""

    node_id: str
    hostname: str
    version: str
    region: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id must be non-empty")
        if not self.hostname.strip():
            raise ValueError("hostname must be non-empty")
        if not self.version.strip():
            raise ValueError("version must be non-empty")
        if not self.region.strip():
            raise ValueError("region must be non-empty")


@dataclass(frozen=True, slots=True)
class Heartbeat:
    """Read-only resource pulse from a federation node."""

    node_id: str
    cpu: float
    memory: float
    disk: float
    network: float
    battery: float | None
    timestamp: datetime
    protocol_version: str = PROTOCOL_VERSION

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id must be non-empty")
        for name in ("cpu", "memory", "disk", "network"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be in [0, 100]")
        if self.battery is not None and not 0.0 <= self.battery <= 100.0:
            raise ValueError("battery must be in [0, 100] when set")
        if not self.protocol_version.strip():
            raise ValueError("protocol_version must be non-empty")


@dataclass(frozen=True, slots=True)
class FederationSnapshot:
    """Immutable telemetry snapshot published by a node.

    Attributes:
        node: Publisher identity.
        telemetry: Bounded resource metrics (cpu/memory/disk/network/battery).
        context: Non-personal situational keys (intent, load class, etc.).
        graph_hash: Content hash of the publisher's Resource Graph view.
        version: Protocol / snapshot schema version.
    """

    node: NodeIdentity
    telemetry: Mapping[str, float | None]
    context: Mapping[str, Any]
    graph_hash: str
    version: str
    published_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.graph_hash.strip():
            raise ValueError("graph_hash must be non-empty")
        if not self.version.strip():
            raise ValueError("version must be non-empty")
        required = ("cpu", "memory", "disk")
        for key in required:
            if key not in self.telemetry:
                raise ValueError(f"telemetry missing required key: {key}")


@dataclass(frozen=True, slots=True)
class NodeRecord:
    """Registry row for one known node (no private user fields)."""

    identity: NodeIdentity
    status: NodeStatus
    last_seen: datetime
    last_heartbeat: Heartbeat | None = None
    last_snapshot_hash: str = ""

    def __post_init__(self) -> None:
        if self.status not in ("online", "offline", "unknown"):
            raise ValueError(f"invalid status: {self.status}")


@dataclass(frozen=True, slots=True)
class RegistryView:
    """Immutable aggregate view of the federation registry."""

    nodes: tuple[NodeRecord, ...]
    last_seen: datetime | None
    status: Literal["healthy", "degraded", "empty"]
    protocol_version: str = PROTOCOL_VERSION
    online_count: int = 0
    offline_count: int = 0
    unknown_count: int = 0

    def __post_init__(self) -> None:
        if self.online_count < 0 or self.offline_count < 0 or self.unknown_count < 0:
            raise ValueError("counts must be non-negative")
