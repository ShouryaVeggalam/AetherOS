"""Topology traversal — immutable queries over TopologyGraph."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence

from aetheros.topology.graph import WORLD_ID, adjacency, entity_ids
from aetheros.topology.models import (
    Cluster,
    ClusterHealth,
    Datacenter,
    Region,
    RegionSummary,
    RelationType,
    TopologyGraph,
    TopologyNode,
)


def get_region(graph: TopologyGraph, region_id: str) -> Region | None:
    rid = region_id.strip().lower()
    for region in graph.regions:
        if region.id == rid or region.id == region_id:
            return region
    return None


def get_datacenter(graph: TopologyGraph, datacenter_id: str) -> Datacenter | None:
    for dc in graph.datacenters:
        if dc.id == datacenter_id:
            return dc
    return None


def get_cluster(graph: TopologyGraph, cluster_id: str) -> Cluster | None:
    for cluster in graph.clusters:
        if cluster.id == cluster_id:
            return cluster
    return None


def get_nodes(
    graph: TopologyGraph,
    *,
    cluster_id: str | None = None,
    region_id: str | None = None,
    status: str | None = None,
) -> tuple[TopologyNode, ...]:
    """Return nodes filtered by optional cluster, region, or status."""

    out: list[TopologyNode] = []
    rid = region_id.strip().lower() if region_id else None
    for node in graph.nodes:
        if cluster_id is not None and node.cluster_id != cluster_id:
            continue
        if rid is not None and node.region_id != rid:
            continue
        if status is not None and node.status != status:
            continue
        out.append(node)
    return tuple(out)


def find_path(
    graph: TopologyGraph,
    source_id: str,
    target_id: str,
    *,
    relations: Sequence[RelationType] | None = None,
) -> tuple[str, ...]:
    """BFS shortest path over directed edges (optional relation filter)."""

    if source_id == target_id:
        if source_id in entity_ids(graph) or source_id == WORLD_ID:
            return (source_id,)
        return ()
    adj = adjacency(graph, relations=relations)
    # Ensure world reachable keys exist
    if WORLD_ID not in adj and any(e.source_id == WORLD_ID for e in graph.edges):
        pass
    queue: deque[str] = deque([source_id])
    prev: dict[str, str | None] = {source_id: None}
    while queue:
        current = queue.popleft()
        for nxt in adj.get(current, ()):
            if nxt in prev:
                continue
            prev[nxt] = current
            if nxt == target_id:
                return _reconstruct(prev, target_id)
            queue.append(nxt)
    return ()


def cluster_health(graph: TopologyGraph, cluster_id: str) -> ClusterHealth | None:
    cluster = get_cluster(graph, cluster_id)
    if cluster is None:
        return None
    nodes = get_nodes(graph, cluster_id=cluster_id)
    online = sum(1 for n in nodes if n.status == "online")
    offline = sum(1 for n in nodes if n.status == "offline")
    unknown = sum(1 for n in nodes if n.status == "unknown")
    total = len(nodes)
    if total == 0:
        status: str = "empty"
    elif offline == total:
        status = "critical"
    elif offline > 0 or unknown > 0:
        status = "degraded"
    else:
        status = "healthy"
    return ClusterHealth(
        cluster_id=cluster.id,
        name=cluster.name,
        node_count=total,
        online=online,
        offline=offline,
        unknown=unknown,
        status=status,  # type: ignore[arg-type]
    )


def region_summary(graph: TopologyGraph, region_id: str) -> RegionSummary | None:
    region = get_region(graph, region_id)
    if region is None:
        return None
    dcs = tuple(d for d in graph.datacenters if d.region_id == region.id)
    dc_ids = {d.id for d in dcs}
    clusters = tuple(c for c in graph.clusters if c.datacenter_id in dc_ids)
    nodes = get_nodes(graph, region_id=region.id)
    return RegionSummary(
        region_id=region.id,
        name=region.name,
        country=region.country,
        datacenter_count=len(dcs),
        cluster_count=len(clusters),
        node_count=len(nodes),
        online_nodes=sum(1 for n in nodes if n.status == "online"),
    )


def all_cluster_health(graph: TopologyGraph) -> tuple[ClusterHealth, ...]:
    out: list[ClusterHealth] = []
    for cluster in graph.clusters:
        health = cluster_health(graph, cluster.id)
        if health is not None:
            out.append(health)
    return tuple(out)


def all_region_summaries(graph: TopologyGraph) -> tuple[RegionSummary, ...]:
    out: list[RegionSummary] = []
    for region in graph.regions:
        summary = region_summary(graph, region.id)
        if summary is not None:
            out.append(summary)
    return tuple(out)


def _reconstruct(prev: dict[str, str | None], target: str) -> tuple[str, ...]:
    path: list[str] = [target]
    while prev[path[-1]] is not None:
        path.append(prev[path[-1]])  # type: ignore[arg-type]
    path.reverse()
    return tuple(path)
