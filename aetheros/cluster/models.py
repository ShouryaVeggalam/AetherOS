"""Cluster / multi-device data contracts for AetherOS v1.4.

Immutable node snapshots only. Read-only — never executes remote commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

NodeHealth = Literal["healthy", "warning", "critical", "offline"]
NodeRole = Literal["laptop", "desktop", "pi", "cloud", "unknown"]


@dataclass(frozen=True, slots=True)
class ClusterNode:
    """One immutable view of a cluster member.

    Attributes:
        node_id: Stable unique identifier for the node.
        hostname: Reported hostname.
        platform: OS / platform string (e.g. Darwin, Linux).
        cpu: CPU percent 0–100.
        memory: Memory percent 0–100.
        disk: Disk percent 0–100.
        battery: Battery percent, or None if unavailable.
        latency: Observed transport latency in milliseconds.
        last_seen: UTC timestamp of the latest telemetry/heartbeat.
    """

    node_id: str
    hostname: str
    platform: str
    cpu: float
    memory: float
    disk: float
    battery: float | None
    latency: float
    last_seen: datetime


@dataclass(frozen=True, slots=True)
class Heartbeat:
    """One heartbeat pulse from a cluster agent.

    Attributes:
        node_id: Node that sent the heartbeat.
        timestamp: When the heartbeat was produced (UTC).
        online: Whether the agent considers itself online.
    """

    node_id: str
    timestamp: datetime
    online: bool


@dataclass(frozen=True, slots=True)
class ClusterAlert:
    """Read-only cluster alert for the dashboard.

    Attributes:
        severity: warning or critical (informational only).
        title: Short alert label.
        description: Traceable explanation grounded in aggregate data.
        node_id: Related node, if any.
    """

    severity: Literal["warning", "critical"]
    title: str
    description: str
    node_id: str | None = None


@dataclass(frozen=True, slots=True)
class ClusterSnapshot:
    """Immutable aggregate view of the whole cluster.

    Attributes:
        total_nodes: Registered node count.
        online_nodes: Nodes seen within the online window.
        offline_nodes: Nodes considered offline.
        average_cpu: Mean CPU across online nodes.
        average_memory: Mean memory across online nodes.
        average_load: Combined load proxy (avg of cpu/memory).
        highest_load_node: Node with the highest CPU, or None.
        nodes: All known nodes (online and offline).
        alerts: Derived cluster alerts (no automatic actions).
    """

    total_nodes: int
    online_nodes: int
    offline_nodes: int
    average_cpu: float
    average_memory: float
    average_load: float
    highest_load_node: ClusterNode | None
    nodes: tuple[ClusterNode, ...]
    alerts: tuple[ClusterAlert, ...]
