"""Node helpers — health classification and payload decoding.

Read-only. Never executes commands on remote machines.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aetheros.cluster.models import ClusterNode, NodeHealth


def classify_health(
    node: ClusterNode,
    *,
    online: bool,
    warn_cpu: float = 70.0,
    critical_cpu: float = 90.0,
) -> NodeHealth:
    """Classify node health for color-coded display only.

    Args:
        node: Latest node snapshot.
        online: Whether heartbeat / last_seen is within the online window.
        warn_cpu: CPU threshold for warning.
        critical_cpu: CPU threshold for critical.

    Returns:
        healthy, warning, critical, or offline — never triggers actions.
    """

    if not online:
        return "offline"
    if node.cpu >= critical_cpu or node.memory >= 95.0:
        return "critical"
    if node.cpu >= warn_cpu or node.memory >= 85.0 or node.disk >= 90.0:
        return "warning"
    return "healthy"


def health_style(health: NodeHealth) -> str:
    """Map health to a Rich style name (color coding only)."""

    return {
        "healthy": "green",
        "warning": "yellow",
        "critical": "red",
        "offline": "dim",
    }.get(health, "white")


def node_from_payload(payload: dict[str, Any]) -> ClusterNode:
    """Build a ClusterNode from a transport telemetry payload."""

    stamp = _parse_stamp(str(payload.get("last_seen", "")))
    battery_raw = payload.get("battery")
    battery = None if battery_raw is None else float(battery_raw)
    return ClusterNode(
        node_id=str(payload["node_id"]),
        hostname=str(payload.get("hostname", payload["node_id"])),
        platform=str(payload.get("platform", "unknown")),
        cpu=float(payload.get("cpu", 0.0)),
        memory=float(payload.get("memory", 0.0)),
        disk=float(payload.get("disk", 0.0)),
        battery=battery,
        latency=float(payload.get("latency", 0.0)),
        last_seen=stamp,
    )


def node_to_payload(node: ClusterNode) -> dict[str, Any]:
    """Serialize a ClusterNode into a JSON-compatible payload."""

    return {
        "node_id": node.node_id,
        "hostname": node.hostname,
        "platform": node.platform,
        "cpu": node.cpu,
        "memory": node.memory,
        "disk": node.disk,
        "battery": node.battery,
        "latency": node.latency,
        "last_seen": node.last_seen.isoformat(),
    }


def _parse_stamp(value: str) -> datetime:
    """Parse an ISO timestamp into timezone-aware UTC."""

    if not value:
        return datetime.now(UTC)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed
