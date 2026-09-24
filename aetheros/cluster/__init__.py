"""AetherOS v1.4 — Multi-Device / Cluster Intelligence.

Distributed read-only telemetry aggregation. No remote command execution.
"""

from __future__ import annotations

from aetheros.cluster.aggregator import aggregate, derive_alerts
from aetheros.cluster.heartbeat import HeartbeatTracker, make_heartbeat_message
from aetheros.cluster.models import (
    ClusterAlert,
    ClusterNode,
    ClusterSnapshot,
    Heartbeat,
)
from aetheros.cluster.node import classify_health, health_style, node_from_payload
from aetheros.cluster.registry import NodeRegistry
from aetheros.cluster.renderer import ClusterPanel
from aetheros.cluster.transport import (
    LocalJSONTransport,
    TransportMessage,
    utc_now,
)

__all__ = [
    "ClusterAlert",
    "ClusterNode",
    "ClusterPanel",
    "ClusterSnapshot",
    "Heartbeat",
    "HeartbeatTracker",
    "LocalJSONTransport",
    "NodeRegistry",
    "TransportMessage",
    "aggregate",
    "classify_health",
    "derive_alerts",
    "health_style",
    "make_heartbeat_message",
    "node_from_payload",
    "utc_now",
]
