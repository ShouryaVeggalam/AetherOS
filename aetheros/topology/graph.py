"""Topology graph primitives — immutable edges and adjacency indexes."""

from __future__ import annotations

from collections.abc import Sequence

from aetheros.topology.models import (
    Cluster,
    Datacenter,
    Region,
    RelationType,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
)

WORLD_ID = "world"


def edge(
    source_id: str,
    target_id: str,
    relation: RelationType,
    *,
    weight: float = 1.0,
) -> TopologyEdge:
    return TopologyEdge(
        source_id=source_id,
        target_id=target_id,
        relation=relation,
        weight=weight,
    )


def hierarchy_edges(
    *,
    regions: Sequence[Region],
    datacenters: Sequence[Datacenter],
    clusters: Sequence[Cluster],
    nodes: Sequence[TopologyNode],
) -> tuple[TopologyEdge, ...]:
    """Build CONTAINS / HOSTS edges for the canonical hierarchy."""

    out: list[TopologyEdge] = []
    for region in regions:
        out.append(edge(WORLD_ID, region.id, "CONTAINS"))
    for dc in datacenters:
        out.append(edge(dc.region_id, dc.id, "CONTAINS"))
        out.append(edge(dc.id, dc.region_id, "DEPENDS_ON", weight=0.1))
    for cluster in clusters:
        out.append(edge(cluster.datacenter_id, cluster.id, "HOSTS"))
    for node in nodes:
        if node.cluster_id:
            out.append(edge(node.cluster_id, node.node_id, "HOSTS"))
    return tuple(out)


def connect_nodes(
    pairs: Sequence[tuple[str, str]],
    *,
    relation: RelationType = "CONNECTED_TO",
) -> tuple[TopologyEdge, ...]:
    """Peer CONNECTED_TO / REPLICATES edges when both endpoints exist."""

    return tuple(edge(a, b, relation) for a, b in pairs if a and b and a != b)


def adjacency(
    graph: TopologyGraph,
    *,
    relations: Sequence[RelationType] | None = None,
) -> dict[str, tuple[str, ...]]:
    """Forward adjacency filtered by optional relation types."""

    allowed = set(relations) if relations is not None else None
    buckets: dict[str, list[str]] = {}
    for e in graph.edges:
        if allowed is not None and e.relation not in allowed:
            continue
        buckets.setdefault(e.source_id, []).append(e.target_id)
    return {k: tuple(sorted(set(v))) for k, v in buckets.items()}


def entity_ids(graph: TopologyGraph) -> frozenset[str]:
    ids = {WORLD_ID}
    ids.update(r.id for r in graph.regions)
    ids.update(d.id for d in graph.datacenters)
    ids.update(c.id for c in graph.clusters)
    ids.update(n.node_id for n in graph.nodes)
    return frozenset(ids)
