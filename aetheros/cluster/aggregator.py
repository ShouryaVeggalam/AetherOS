"""Cluster aggregator — immutable multi-node summaries.

Calculates averages, highest load, offline counts, and alerts.
Never triggers remediation actions.
"""

from __future__ import annotations

from aetheros.cluster.models import ClusterAlert, ClusterNode, ClusterSnapshot
from aetheros.cluster.registry import NodeRegistry


def aggregate(registry: NodeRegistry) -> ClusterSnapshot:
    """Build an immutable ClusterSnapshot from the registry.

    Args:
        registry: Node registry with latest telemetry and heartbeats.

    Returns:
        Immutable aggregate snapshot for the dashboard.
    """

    nodes = registry.nodes()
    online = tuple(n for n in nodes if registry.is_online(n.node_id))
    offline_count = len(nodes) - len(online)
    if online:
        avg_cpu = sum(n.cpu for n in online) / len(online)
        avg_mem = sum(n.memory for n in online) / len(online)
        avg_load = (avg_cpu + avg_mem) / 2.0
        highest = max(online, key=lambda n: n.cpu)
    else:
        avg_cpu = 0.0
        avg_mem = 0.0
        avg_load = 0.0
        highest = None
    alerts = derive_alerts(online, avg_cpu)
    return ClusterSnapshot(
        total_nodes=len(nodes),
        online_nodes=len(online),
        offline_nodes=offline_count,
        average_cpu=round(avg_cpu, 1),
        average_memory=round(avg_mem, 1),
        average_load=round(avg_load, 1),
        highest_load_node=highest,
        nodes=nodes,
        alerts=alerts,
    )


def derive_alerts(
    online: tuple[ClusterNode, ...],
    average_cpu: float,
) -> tuple[ClusterAlert, ...]:
    """Derive read-only alerts from online node metrics."""

    if not online:
        return ()
    alerts: list[ClusterAlert] = []
    for node in online:
        delta = node.cpu - average_cpu
        if delta >= 40.0:
            alerts.append(
                ClusterAlert(
                    severity="critical",
                    title="High relative load",
                    description=(
                        f"{node.hostname} exceeds cluster average by " f"{delta:.0f}%."
                    ),
                    node_id=node.node_id,
                )
            )
        elif delta >= 25.0:
            alerts.append(
                ClusterAlert(
                    severity="warning",
                    title="Above cluster average",
                    description=(
                        f"{node.hostname} exceeds cluster average by " f"{delta:.0f}%."
                    ),
                    node_id=node.node_id,
                )
            )
        if node.cpu >= 90.0:
            alerts.append(
                ClusterAlert(
                    severity="critical",
                    title="Critical CPU",
                    description=f"{node.hostname} CPU at {node.cpu:.0f}%.",
                    node_id=node.node_id,
                )
            )
    return tuple(alerts)
