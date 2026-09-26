"""Cluster Topology models — immutable hierarchical infrastructure graph.

v4.0 P2. World → Regions → Datacenters → Clusters → Nodes.
Models infrastructure only. Never represents remote control or SSH.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

from aetheros.federation.models import Heartbeat, NodeStatus

RelationType = Literal[
    "CONTAINS",
    "HOSTS",
    "CONNECTED_TO",
    "REPLICATES",
    "DEPENDS_ON",
]

EntityKind = Literal["world", "region", "datacenter", "cluster", "node"]


@dataclass(frozen=True, slots=True)
class Region:
    """Geographic region in the topology hierarchy."""

    id: str
    name: str
    country: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        if not self.country.strip():
            raise ValueError("country must be non-empty")


@dataclass(frozen=True, slots=True)
class Datacenter:
    """Datacenter hosted within a region."""

    id: str
    region_id: str
    name: str
    capacity: int

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.region_id.strip():
            raise ValueError("region_id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        if self.capacity < 0:
            raise ValueError("capacity must be >= 0")


@dataclass(frozen=True, slots=True)
class Cluster:
    """Compute cluster hosted within a datacenter."""

    id: str
    datacenter_id: str
    name: str
    node_count: int

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.datacenter_id.strip():
            raise ValueError("datacenter_id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        if self.node_count < 0:
            raise ValueError("node_count must be >= 0")


@dataclass(frozen=True, slots=True)
class TopologyNode:
    """Leaf infrastructure node (federation member) in the topology."""

    node_id: str
    hostname: str
    status: NodeStatus
    version: str
    heartbeat: Heartbeat | None = None
    cluster_id: str = ""
    region_id: str = ""

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id must be non-empty")
        if not self.hostname.strip():
            raise ValueError("hostname must be non-empty")
        if self.status not in ("online", "offline", "unknown"):
            raise ValueError(f"invalid status: {self.status}")
        if not self.version.strip():
            raise ValueError("version must be non-empty")


@dataclass(frozen=True, slots=True)
class TopologyEdge:
    """Immutable directed relationship between topology entities."""

    source_id: str
    target_id: str
    relation: RelationType
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id must be non-empty")
        if not self.target_id.strip():
            raise ValueError("target_id must be non-empty")
        if self.relation not in (
            "CONTAINS",
            "HOSTS",
            "CONNECTED_TO",
            "REPLICATES",
            "DEPENDS_ON",
        ):
            raise ValueError(f"invalid relation: {self.relation}")
        if self.weight < 0:
            raise ValueError("weight must be >= 0")


@dataclass(frozen=True, slots=True)
class TopologyGraph:
    """Canonical immutable distributed infrastructure graph for Atlas."""

    regions: tuple[Region, ...]
    datacenters: tuple[Datacenter, ...]
    clusters: tuple[Cluster, ...]
    nodes: tuple[TopologyNode, ...]
    edges: tuple[TopologyEdge, ...]
    built_at: datetime | None = None

    def __post_init__(self) -> None:
        region_ids = {r.id for r in self.regions}
        dc_ids = {d.id for d in self.datacenters}
        cluster_ids = {c.id for c in self.clusters}
        for dc in self.datacenters:
            if dc.region_id not in region_ids:
                raise ValueError(f"datacenter region missing: {dc.region_id}")
        for cluster in self.clusters:
            if cluster.datacenter_id not in dc_ids:
                raise ValueError(f"cluster datacenter missing: {cluster.datacenter_id}")
        for node in self.nodes:
            if node.cluster_id and node.cluster_id not in cluster_ids:
                raise ValueError(f"node cluster missing: {node.cluster_id}")


@dataclass(frozen=True, slots=True)
class ClusterHealth:
    """Immutable health summary for one cluster."""

    cluster_id: str
    name: str
    node_count: int
    online: int
    offline: int
    unknown: int
    status: Literal["healthy", "degraded", "critical", "empty"]


@dataclass(frozen=True, slots=True)
class RegionSummary:
    """Immutable summary for one region."""

    region_id: str
    name: str
    country: str
    datacenter_count: int
    cluster_count: int
    node_count: int
    online_nodes: int
