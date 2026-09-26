"""Horizon Topology — region → datacenter → cluster → node hierarchy.

Consumes TopologyGraph. Presentation only.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.horizon.snapshot import HorizonSnapshot
from aetheros.horizon.widgets.tree import tree_from_paths


def render_topology(snapshot: HorizonSnapshot) -> RenderableType:
    """Render topology hierarchy from an immutable TopologyGraph."""

    graph = snapshot.topology_graph
    if graph is None:
        body = Text(
            "TOPOLOGY idle.\nNo TopologyGraph in snapshot.\nRead-only.",
            style="dim",
        )
        return Panel(body, title="Horizon · Topology", border_style="bright_white")

    paths: list[tuple[str, ...]] = []
    nodes = tuple(getattr(graph, "nodes", ()) or ())
    for node in nodes:
        region = str(
            getattr(node, "region_id", None) or getattr(node, "region", "region")
        )
        dc = str(
            getattr(node, "datacenter_id", None)
            or getattr(node, "datacenter", "datacenter")
        )
        cluster = str(
            getattr(node, "cluster_id", None) or getattr(node, "cluster", "cluster")
        )
        node_id = str(getattr(node, "node_id", None) or getattr(node, "id", "node"))
        paths.append((region, dc, cluster, node_id))

    if not paths:
        # Fall back to region/cluster listings if present.
        for region in tuple(getattr(graph, "regions", ()) or ()):
            rid = str(
                getattr(region, "region_id", None) or getattr(region, "id", region)
            )
            paths.append((rid,))

    tree = tree_from_paths("World", paths)
    body = Group(
        Text("TOPOLOGY", style="bold bright_white"),
        Text("Region → Datacenter → Cluster → Node", style="dim"),
        Text(""),
        tree,
        Text(""),
        Text(
            f"Regions {snapshot.regions} · Clusters {snapshot.clusters} · "
            f"Nodes {snapshot.nodes}",
            style="dim",
        ),
    )
    return Panel(body, title="Horizon · Topology", border_style="bright_white")
