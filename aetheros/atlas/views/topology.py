"""Atlas Topology — World → Regions → DCs → Clusters → Nodes as Rich Tree.

Consumes TopologyGraph evidence only. Never fabricates geography.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.atlas.snapshot import AtlasSnapshot
from aetheros.atlas.widgets.tree import AtlasTree, TreeNodeSpec


def render_topology(snapshot: AtlasSnapshot) -> RenderableType:
    """Render infrastructure hierarchy from a TopologyGraph snapshot."""

    graph = snapshot.topology_graph
    if graph is None:
        body = Text(
            "TOPOLOGY idle.\nNo TopologyGraph evidence in snapshot.\nRead-only.",
            style="dim",
        )
        return Panel(body, title="Atlas · Topology", border_style="bright_green")

    tree = _build_tree(graph)
    regions = len(getattr(graph, "regions", ()) or ())
    nodes = len(getattr(graph, "nodes", ()) or ())
    body = Group(
        Text("TOPOLOGY", style="bold bright_green"),
        Text("World → Regions → Datacenters → Clusters → Nodes", style="dim"),
        Text(""),
        tree,
        Text(""),
        Text(f"Regions {regions} · Nodes {nodes}", style="dim"),
    )
    return Panel(body, title="Atlas · Topology", border_style="bright_green")


def _build_tree(graph: object) -> AtlasTree:
    regions = tuple(getattr(graph, "regions", ()) or ())
    datacenters = tuple(getattr(graph, "datacenters", ()) or ())
    clusters = tuple(getattr(graph, "clusters", ()) or ())
    nodes = tuple(getattr(graph, "nodes", ()) or ())

    dcs_by_region: dict[str, list] = {}
    for dc in datacenters:
        dcs_by_region.setdefault(str(getattr(dc, "region_id", "")), []).append(dc)
    clusters_by_dc: dict[str, list] = {}
    for cluster in clusters:
        clusters_by_dc.setdefault(
            str(getattr(cluster, "datacenter_id", "")), []
        ).append(cluster)
    nodes_by_cluster: dict[str, list] = {}
    for node in nodes:
        nodes_by_cluster.setdefault(str(getattr(node, "cluster_id", "")), []).append(
            node
        )

    region_specs: list[TreeNodeSpec] = []
    for region in regions:
        rid = str(getattr(region, "id", ""))
        r_name = str(getattr(region, "name", rid))
        dc_specs: list[TreeNodeSpec] = []
        for dc in dcs_by_region.get(rid, []):
            did = str(getattr(dc, "id", ""))
            d_name = str(getattr(dc, "name", did))
            c_specs: list[TreeNodeSpec] = []
            for cluster in clusters_by_dc.get(did, []):
                cid = str(getattr(cluster, "id", ""))
                c_name = str(getattr(cluster, "name", cid))
                n_specs = tuple(
                    TreeNodeSpec(
                        label=str(
                            getattr(node, "hostname", None)
                            or getattr(node, "node_id", "?")
                        ),
                        style=_status_style(str(getattr(node, "status", "unknown"))),
                    )
                    for node in nodes_by_cluster.get(cid, [])
                )
                c_specs.append(
                    TreeNodeSpec(label=c_name, style="cyan", children=n_specs)
                )
            dc_specs.append(TreeNodeSpec(label=d_name, children=tuple(c_specs)))
        region_specs.append(
            TreeNodeSpec(label=r_name, style="bold", children=tuple(dc_specs))
        )
    return AtlasTree(root_label="WORLD", children=tuple(region_specs))


def _status_style(status: str) -> str:
    if status == "online":
        return "bright_green"
    if status == "offline":
        return "red"
    return "yellow"
