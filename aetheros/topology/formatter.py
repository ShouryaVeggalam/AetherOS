"""Rich formatter for Cluster Topology Engine (dashboard shortcut Z).

T remains Observatory graph toggle. Z opens Topology views.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from aetheros.topology.models import TopologyGraph
from aetheros.topology.traversal import (
    all_cluster_health,
    all_region_summaries,
    get_nodes,
)


@dataclass(frozen=True, slots=True)
class TopologyPanel:
    """Center-panel renderable for Cluster Topology (shortcut Z)."""

    graph: TopologyGraph | None = None
    view: str = "tree"

    def __rich__(self) -> RenderableType:
        if self.graph is None or (not self.graph.regions and not self.graph.nodes):
            return Panel(
                Text(
                    "TOPOLOGY idle.\n"
                    "World → Regions → Datacenters → Clusters → Nodes.\n"
                    "Built from Federation Registry only — never fabricated.\n"
                    "Z opens this page · T remains graph metric toggle.\n"
                    "Status: Read-only infrastructure model",
                    style="dim",
                ),
                title="Cluster Topology",
                border_style="bright_green",
            )

        view = self.view.lower()
        if view == "world":
            body = self._world_view()
        elif view == "regions":
            body = self._regions_view()
        elif view == "clusters":
            body = self._clusters_view()
        elif view == "health":
            body = self._health_view()
        else:
            body = self._tree_view()
        return Panel(body, title="Cluster Topology", border_style="bright_green")

    def _tree_view(self) -> RenderableType:
        assert self.graph is not None
        tree = Tree(Text("WORLD", style="bold bright_green"))
        dcs_by_region: dict[str, list] = {}
        for dc in self.graph.datacenters:
            dcs_by_region.setdefault(dc.region_id, []).append(dc)
        clusters_by_dc: dict[str, list] = {}
        for cluster in self.graph.clusters:
            clusters_by_dc.setdefault(cluster.datacenter_id, []).append(cluster)
        nodes_by_cluster: dict[str, list] = {}
        for node in self.graph.nodes:
            nodes_by_cluster.setdefault(node.cluster_id, []).append(node)

        for region in self.graph.regions:
            r_branch = tree.add(
                Text(f"{region.name}  ({region.country})", style="bold")
            )
            for dc in dcs_by_region.get(region.id, []):
                d_branch = r_branch.add(Text(dc.name))
                for cluster in clusters_by_dc.get(dc.id, []):
                    c_branch = d_branch.add(Text(cluster.name, style="cyan"))
                    for node in nodes_by_cluster.get(cluster.id, []):
                        c_branch.add(
                            Text(
                                f"{node.hostname} [{node.status}]",
                                style=_status_style(node.status),
                            )
                        )
        parts = Group(
            tree,
            Text(""),
            Text("View", style="dim"),
            Text("  Infrastructure Tree  (] cycles)"),
        )
        return parts

    def _world_view(self) -> RenderableType:
        assert self.graph is not None
        g = self.graph
        parts: list[Text] = [
            Text("TOPOLOGY", style="bold bright_green"),
            Text(""),
            Text("World", style="bold"),
            Text(f"  Regions       {len(g.regions)}"),
            Text(f"  Datacenters   {len(g.datacenters)}"),
            Text(f"  Clusters      {len(g.clusters)}"),
            Text(f"  Nodes         {len(g.nodes)}"),
            Text(f"  Edges         {len(g.edges)}"),
            Text(""),
            Text("View", style="dim"),
            Text("  World  (] cycles)"),
        ]
        return Group(*parts)

    def _regions_view(self) -> RenderableType:
        assert self.graph is not None
        parts: list[Text] = [
            Text("TOPOLOGY", style="bold bright_green"),
            Text(""),
            Text("Regions", style="bold"),
            Text(""),
        ]
        summaries = all_region_summaries(self.graph)
        if not summaries:
            parts.append(Text("  (none)", style="dim"))
        for s in summaries:
            parts.append(
                Text(
                    f"  · {s.name:<18} {s.country:<16} "
                    f"dc={s.datacenter_count} cl={s.cluster_count} "
                    f"nodes={s.node_count} online={s.online_nodes}"
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Regions  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _clusters_view(self) -> RenderableType:
        assert self.graph is not None
        parts: list[Text] = [
            Text("TOPOLOGY", style="bold bright_green"),
            Text(""),
            Text("Clusters", style="bold"),
            Text(""),
        ]
        if not self.graph.clusters:
            parts.append(Text("  (none)", style="dim"))
        for cluster in self.graph.clusters:
            nodes = get_nodes(self.graph, cluster_id=cluster.id)
            parts.append(
                Text(
                    f"  · {cluster.name:<24} nodes={len(nodes)} "
                    f"dc={cluster.datacenter_id}"
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Clusters  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _health_view(self) -> RenderableType:
        assert self.graph is not None
        parts: list[Text] = [
            Text("TOPOLOGY", style="bold bright_green"),
            Text(""),
            Text("Node Health", style="bold"),
            Text(""),
        ]
        healths = all_cluster_health(self.graph)
        if not healths:
            parts.append(Text("  (none)", style="dim"))
        for h in healths:
            parts.append(
                Text(
                    f"  · {h.name:<24} {h.status:<10} "
                    f"up={h.online} down={h.offline} unk={h.unknown}"
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Node Health  (] cycles)"),
            ]
        )
        return Group(*parts)


def _status_style(status: str) -> str:
    if status == "online":
        return "green"
    if status == "offline":
        return "red"
    return "yellow"
