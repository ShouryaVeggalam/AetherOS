"""Topology builder — construct TopologyGraph from Federation Registry.

Never fabricates infrastructure. Regions come from observed node identities.
Datacenters/clusters come from provided catalogs that match observed regions,
or deterministic unassigned placeholders when nodes lack explicit placement.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from aetheros.federation.models import NodeRecord, RegistryView
from aetheros.federation.registry import FederationRegistry
from aetheros.topology.clusters import select_clusters
from aetheros.topology.datacenters import select_datacenters
from aetheros.topology.graph import connect_nodes, hierarchy_edges
from aetheros.topology.models import (
    Cluster,
    Datacenter,
    Region,
    TopologyGraph,
    TopologyNode,
)
from aetheros.topology.regions import select_regions


@dataclass(frozen=True, slots=True)
class NodePlacement:
    """Optional explicit placement of a federation node into topology."""

    node_id: str
    cluster_id: str
    datacenter_id: str = ""


@dataclass(frozen=True, slots=True)
class TopologyMetadata:
    """Evidence-backed catalogs used while building topology.

    Only entries that intersect observed federation nodes/regions are used.
    """

    regions: Mapping[str, Region] = field(default_factory=dict)
    datacenters: tuple[Datacenter, ...] = ()
    clusters: tuple[Cluster, ...] = ()
    placements: tuple[NodePlacement, ...] = ()
    peer_links: tuple[tuple[str, str], ...] = ()
    replicate_links: tuple[tuple[str, str], ...] = ()


def build_topology(
    registry: FederationRegistry | RegistryView,
    *,
    metadata: TopologyMetadata | None = None,
    now: datetime | None = None,
) -> TopologyGraph:
    """Build an immutable topology graph from connected federation nodes."""

    stamp = now or datetime.now(UTC)
    meta = metadata or TopologyMetadata()
    view = registry.view() if isinstance(registry, FederationRegistry) else registry
    records = view.nodes
    if not records:
        return TopologyGraph(
            regions=(),
            datacenters=(),
            clusters=(),
            nodes=(),
            edges=(),
            built_at=stamp,
        )

    placement_by_node = {p.node_id: p for p in meta.placements}
    cluster_catalog = {c.id: c for c in meta.clusters}

    region_ids = [rec.identity.region for rec in records]
    regions = select_regions(region_ids, catalog=meta.regions)

    # Resolve placement or fall back to unassigned chain per region.
    node_cluster: dict[str, str] = {}
    need_unassigned_dc: set[str] = set()
    need_unassigned_cluster_dc: set[str] = set()

    for rec in records:
        rid = rec.identity.region.strip().lower() or "unknown"
        place = placement_by_node.get(rec.identity.node_id)
        if place is not None and place.cluster_id in cluster_catalog:
            cluster = cluster_catalog[place.cluster_id]
            node_cluster[rec.identity.node_id] = cluster.id
        else:
            need_unassigned_dc.add(rid)

    datacenters = select_datacenters(
        regions,
        catalog=meta.datacenters,
        require_unassigned_for=tuple(need_unassigned_dc),
    )
    dc_by_region_unassigned = {
        d.region_id: d for d in datacenters if d.id.startswith("dc-unassigned-")
    }

    for rec in records:
        nid = rec.identity.node_id
        if nid in node_cluster:
            continue
        rid = rec.identity.region.strip().lower() or "unknown"
        dc = dc_by_region_unassigned.get(rid)
        if dc is None:
            continue
        need_unassigned_cluster_dc.add(dc.id)

    # Count nodes per cluster (including pending unassigned)
    pending_counts: dict[str, int] = {}
    for rec in records:
        nid = rec.identity.node_id
        if nid in node_cluster:
            cid = node_cluster[nid]
            pending_counts[cid] = pending_counts.get(cid, 0) + 1
        else:
            rid = rec.identity.region.strip().lower() or "unknown"
            dc = dc_by_region_unassigned.get(rid)
            if dc is not None:
                cid = f"cluster-unassigned-{dc.id}"
                node_cluster[nid] = cid
                pending_counts[cid] = pending_counts.get(cid, 0) + 1

    clusters = select_clusters(
        datacenters,
        catalog=meta.clusters,
        require_unassigned_for=tuple(need_unassigned_cluster_dc),
        node_counts=pending_counts,
    )

    nodes = tuple(_to_node(rec, node_cluster) for rec in records)
    edges = hierarchy_edges(
        regions=regions,
        datacenters=datacenters,
        clusters=clusters,
        nodes=nodes,
    )
    known_ids = (
        {r.id for r in regions}
        | {d.id for d in datacenters}
        | {c.id for c in clusters}
        | {n.node_id for n in nodes}
    )
    peers = tuple(
        (a, b) for a, b in meta.peer_links if a in known_ids and b in known_ids
    )
    reps = tuple(
        (a, b) for a, b in meta.replicate_links if a in known_ids and b in known_ids
    )
    edges = edges + connect_nodes(peers, relation="CONNECTED_TO")
    edges = edges + connect_nodes(reps, relation="REPLICATES")

    return TopologyGraph(
        regions=regions,
        datacenters=datacenters,
        clusters=clusters,
        nodes=nodes,
        edges=edges,
        built_at=stamp,
    )


def build_from_records(
    records: Sequence[NodeRecord],
    *,
    metadata: TopologyMetadata | None = None,
    now: datetime | None = None,
) -> TopologyGraph:
    """Build topology from an explicit tuple of registry records."""

    from aetheros.federation.models import PROTOCOL_VERSION, RegistryView

    view = RegistryView(
        nodes=tuple(records),
        last_seen=None,
        status="healthy" if records else "empty",
        protocol_version=PROTOCOL_VERSION,
        online_count=sum(1 for r in records if r.status == "online"),
        offline_count=sum(1 for r in records if r.status == "offline"),
        unknown_count=sum(1 for r in records if r.status == "unknown"),
    )
    return build_topology(view, metadata=metadata, now=now)


def _to_node(record: NodeRecord, cluster_map: Mapping[str, str]) -> TopologyNode:
    ident = record.identity
    return TopologyNode(
        node_id=ident.node_id,
        hostname=ident.hostname,
        status=record.status,
        version=ident.version,
        heartbeat=record.last_heartbeat,
        cluster_id=cluster_map.get(ident.node_id, ""),
        region_id=ident.region.strip().lower(),
    )
