"""Cluster Topology Engine — v4.0 P2 hierarchical infrastructure graph.

World → Regions → Datacenters → Clusters → Nodes.
Built from Federation Registry. Read-only. Never SSH / remote execution.
"""

from __future__ import annotations

from aetheros.topology.builder import (
    NodePlacement,
    TopologyMetadata,
    build_from_records,
    build_topology,
)
from aetheros.topology.demo import demo_topology_metadata
from aetheros.topology.formatter import TopologyPanel
from aetheros.topology.graph import WORLD_ID, adjacency, entity_ids, hierarchy_edges
from aetheros.topology.models import (
    Cluster,
    ClusterHealth,
    Datacenter,
    Region,
    RegionSummary,
    RelationType,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
)
from aetheros.topology.traversal import (
    all_cluster_health,
    all_region_summaries,
    cluster_health,
    find_path,
    get_cluster,
    get_datacenter,
    get_nodes,
    get_region,
    region_summary,
)

__all__ = [
    "WORLD_ID",
    "Cluster",
    "ClusterHealth",
    "Datacenter",
    "NodePlacement",
    "Region",
    "RegionSummary",
    "RelationType",
    "TopologyEdge",
    "TopologyGraph",
    "TopologyMetadata",
    "TopologyNode",
    "TopologyPanel",
    "adjacency",
    "all_cluster_health",
    "all_region_summaries",
    "build_from_records",
    "build_topology",
    "cluster_health",
    "demo_topology_metadata",
    "entity_ids",
    "find_path",
    "get_cluster",
    "get_datacenter",
    "get_nodes",
    "get_region",
    "hierarchy_edges",
    "region_summary",
]
