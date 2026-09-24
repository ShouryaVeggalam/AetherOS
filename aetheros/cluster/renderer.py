"""Rich renderer for the Cluster Overview panel.

Presentation only. No transport or aggregation logic here.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.cluster.models import ClusterSnapshot, NodeHealth
from aetheros.cluster.node import classify_health, health_style


@dataclass(frozen=True, slots=True)
class ClusterPanel:
    """Center-panel renderable for one ClusterSnapshot."""

    snapshot: ClusterSnapshot | None
    online_ids: frozenset[str] = frozenset()

    def __rich__(self) -> RenderableType:
        """Render the multi-device cluster overview."""

        if self.snapshot is None or self.snapshot.total_nodes == 0:
            return Panel(
                Text(
                    "No cluster nodes yet.\n"
                    "Local agent publishes each second. "
                    "Demo peers appear when seeded.",
                    style="dim",
                ),
                title="Cluster Overview",
                border_style="bright_blue",
            )
        snap = self.snapshot
        body = Group(
            Text("CLUSTER OVERVIEW", style="bold bright_blue"),
            Text(""),
            _summary(snap),
            Text(""),
            _nodes_table(snap, self.online_ids),
            Text(""),
            _alerts(snap),
            Text(""),
            Text("C/ESC leave  ·  read-only  ·  no remote execution", style="dim"),
        )
        return Panel(body, title="Cluster Overview", border_style="bright_blue")


def _summary(snap: ClusterSnapshot) -> Group:
    """Render total / online / averages / highest load."""

    highest = "—"
    if snap.highest_load_node is not None:
        node = snap.highest_load_node
        highest = f"{node.hostname} ({node.cpu:.0f}%)"
    lines = [
        Text(f"Total Nodes:   {snap.total_nodes}"),
        Text(f"Online:        {snap.online_nodes}"),
        Text(f"Offline:       {snap.offline_nodes}"),
        Text(f"Average CPU:   {snap.average_cpu:.0f}%"),
        Text(f"Average Mem:   {snap.average_memory:.0f}%"),
        Text(f"Average Load:  {snap.average_load:.0f}%"),
        Text(f"Highest Load:  {highest}"),
    ]
    return Group(Text("Summary", style="bold cyan"), *lines)


def _nodes_table(snap: ClusterSnapshot, online_ids: frozenset[str]) -> Group:
    """Render per-node rows with health color coding."""

    table = Table(title="Nodes", expand=True, pad_edge=False)
    table.add_column("Host", style="bold")
    table.add_column("CPU", justify="right")
    table.add_column("Mem", justify="right")
    table.add_column("Disk", justify="right")
    table.add_column("Health")
    for node in snap.nodes:
        online = node.node_id in online_ids
        health: NodeHealth = classify_health(node, online=online)
        style = health_style(health)
        table.add_row(
            node.hostname,
            f"{node.cpu:.0f}%",
            f"{node.memory:.0f}%",
            f"{node.disk:.0f}%",
            Text(health.upper(), style=style),
        )
    return Group(table)


def _alerts(snap: ClusterSnapshot) -> Group:
    """Render cluster alerts (informational only)."""

    lines: list[Text] = [Text("Alerts", style="bold cyan")]
    if not snap.alerts:
        lines.append(Text("  None", style="dim"))
        return Group(*lines)
    for alert in snap.alerts[:6]:
        style = "red" if alert.severity == "critical" else "yellow"
        lines.append(Text(f"  • {alert.description}", style=style))
    return Group(*lines)
