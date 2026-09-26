"""Tests for v4.0 P2 Cluster Topology Engine."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from rich.console import Console

from aetheros.federation import FederationRegistry, seed_demo_federation
from aetheros.federation.models import Heartbeat, NodeIdentity, NodeRecord
from aetheros.topology import (
    Cluster,
    Datacenter,
    NodePlacement,
    Region,
    TopologyMetadata,
    TopologyPanel,
    adjacency,
    all_cluster_health,
    all_region_summaries,
    build_from_records,
    build_topology,
    cluster_health,
    demo_topology_metadata,
    find_path,
    get_cluster,
    get_datacenter,
    get_nodes,
    get_region,
    region_summary,
)
from aetheros.topology.graph import WORLD_ID
from aetheros.topology.models import TopologyEdge, TopologyGraph, TopologyNode


def _stamp() -> datetime:
    return datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def _record(
    node_id: str,
    *,
    region: str,
    status: str = "online",
    hostname: str | None = None,
) -> NodeRecord:
    ident = NodeIdentity(
        node_id=node_id,
        hostname=hostname or node_id,
        version="4.0.0",
        region=region,
        created_at=_stamp(),
    )
    hb = Heartbeat(
        node_id=node_id,
        cpu=10,
        memory=20,
        disk=30,
        network=5,
        battery=None,
        timestamp=_stamp(),
    )
    return NodeRecord(
        identity=ident,
        status=status,  # type: ignore[arg-type]
        last_seen=_stamp(),
        last_heartbeat=hb,
    )


# --- models ------------------------------------------------------------------


def test_model_validation() -> None:
    with pytest.raises(ValueError):
        Region(id=" ", name="n", country="c")
    with pytest.raises(ValueError):
        Datacenter(id="d", region_id="r", name=" ", capacity=1)
    with pytest.raises(ValueError):
        Cluster(id="c", datacenter_id="d", name="n", node_count=-1)
    with pytest.raises(ValueError):
        TopologyNode(
            node_id="n",
            hostname="h",
            status="nope",  # type: ignore[arg-type]
            version="1",
        )
    with pytest.raises(ValueError):
        TopologyEdge(source_id="a", target_id="b", relation="NOPE")  # type: ignore[arg-type]


# --- builder / hierarchy -----------------------------------------------------


def test_builder_from_federation_registry() -> None:
    reg = FederationRegistry(online_ttl_sec=60)
    seed_demo_federation(reg, now=_stamp())
    graph = build_topology(reg, metadata=demo_topology_metadata(), now=_stamp())
    assert graph.regions
    assert graph.datacenters
    assert graph.clusters
    assert len(graph.nodes) == 3
    assert any(e.relation == "CONTAINS" for e in graph.edges)
    assert any(e.relation == "HOSTS" for e in graph.edges)
    assert any(e.relation == "CONNECTED_TO" for e in graph.edges)
    assert any(e.relation == "REPLICATES" for e in graph.edges)
    # path world → region
    path = find_path(graph, WORLD_ID, "local", relations=("CONTAINS",))
    assert path[0] == WORLD_ID
    assert "local" in path


def test_builder_never_fabricates_unobserved_regions() -> None:
    records = (_record("n1", region="us-west"),)
    meta = TopologyMetadata(
        regions={
            "us-west": Region(id="us-west", name="US West", country="United States"),
            "asia-south": Region(
                id="asia-south", name="Asia South", country="India"
            ),
        },
        datacenters=(
            Datacenter(
                id="dc-hyd",
                region_id="asia-south",
                name="Hyderabad DC",
                capacity=10,
            ),
            Datacenter(
                id="dc-sfo",
                region_id="us-west",
                name="SFO DC",
                capacity=10,
            ),
        ),
        clusters=(
            Cluster(
                id="cl-asia",
                datacenter_id="dc-hyd",
                name="Asia Cluster",
                node_count=0,
            ),
            Cluster(
                id="cl-west",
                datacenter_id="dc-sfo",
                name="West Cluster",
                node_count=0,
            ),
        ),
        placements=(
            NodePlacement(node_id="n1", cluster_id="cl-west", datacenter_id="dc-sfo"),
        ),
    )
    graph = build_from_records(records, metadata=meta, now=_stamp())
    region_ids = {r.id for r in graph.regions}
    assert "us-west" in region_ids
    assert "asia-south" not in region_ids
    assert all(d.region_id == "us-west" for d in graph.datacenters)


def test_builder_unassigned_when_no_placement() -> None:
    records = (_record("solo", region="eu-central"),)
    graph = build_from_records(records, metadata=TopologyMetadata(), now=_stamp())
    assert graph.regions[0].id == "eu-central"
    assert graph.datacenters[0].id.startswith("dc-unassigned-")
    assert graph.clusters[0].id.startswith("cluster-unassigned-")
    assert graph.nodes[0].cluster_id == graph.clusters[0].id


def test_empty_registry() -> None:
    graph = build_topology(FederationRegistry(), now=_stamp())
    assert graph.nodes == ()
    assert graph.edges == ()


# --- traversal ---------------------------------------------------------------


def test_traversal_getters_and_health() -> None:
    reg = FederationRegistry(online_ttl_sec=60)
    seed_demo_federation(reg, now=_stamp())
    graph = build_topology(reg, metadata=demo_topology_metadata(), now=_stamp())

    assert get_region(graph, "eu-central") is not None
    assert get_datacenter(graph, "dc-fra") is not None
    assert get_cluster(graph, "cluster-gamma") is not None
    nodes = get_nodes(graph, region_id="local")
    assert nodes and nodes[0].region_id == "local"

    health = cluster_health(graph, "cluster-alpha")
    assert health is not None
    assert health.node_count >= 1
    assert health.status in ("healthy", "degraded", "critical", "empty")

    summary = region_summary(graph, "us-west")
    assert summary is not None
    assert summary.cluster_count >= 1
    assert all_cluster_health(graph)
    assert all_region_summaries(graph)

    # offline peer → degraded/critical somewhere
    offline_nodes = get_nodes(graph, status="offline")
    assert offline_nodes


def test_find_path_and_adjacency() -> None:
    reg = FederationRegistry(online_ttl_sec=60)
    seed_demo_federation(reg, now=_stamp())
    graph = build_topology(reg, metadata=demo_topology_metadata(), now=_stamp())
    path = find_path(
        graph,
        "cluster-alpha",
        "node-local",
        relations=("HOSTS",),
    )
    assert path == ("cluster-alpha", "node-local")
    assert find_path(graph, "missing", "also-missing") == ()
    assert find_path(graph, WORLD_ID, WORLD_ID) == (WORLD_ID,)
    adj = adjacency(graph, relations=("HOSTS",))
    assert "cluster-alpha" in adj


# --- formatter ---------------------------------------------------------------


def test_topology_panel_views() -> None:
    reg = FederationRegistry(online_ttl_sec=60)
    seed_demo_federation(reg, now=_stamp())
    graph = build_topology(reg, metadata=demo_topology_metadata(), now=_stamp())
    console = Console(record=True, width=100)
    console.print(TopologyPanel())
    assert "idle" in console.export_text().lower() or "TOPOLOGY" in console.export_text()
    for view in ("tree", "world", "regions", "clusters", "health"):
        console = Console(record=True, width=110)
        console.print(TopologyPanel(graph=graph, view=view))
        text = console.export_text()
        assert "WORLD" in text or "TOPOLOGY" in text


def test_graph_validation_missing_parent() -> None:
    with pytest.raises(ValueError):
        TopologyGraph(
            regions=(),
            datacenters=(
                Datacenter(id="d", region_id="missing", name="D", capacity=1),
            ),
            clusters=(),
            nodes=(),
            edges=(),
        )


def test_coverage_edges() -> None:
    with pytest.raises(ValueError):
        Region(id="r", name=" ", country="c")
    with pytest.raises(ValueError):
        Region(id="r", name="n", country=" ")
    with pytest.raises(ValueError):
        Datacenter(id=" ", region_id="r", name="n", capacity=1)
    with pytest.raises(ValueError):
        Datacenter(id="d", region_id=" ", name="n", capacity=1)
    with pytest.raises(ValueError):
        Datacenter(id="d", region_id="r", name="n", capacity=-1)
    with pytest.raises(ValueError):
        Cluster(id=" ", datacenter_id="d", name="n", node_count=0)
    with pytest.raises(ValueError):
        Cluster(id="c", datacenter_id=" ", name="n", node_count=0)
    with pytest.raises(ValueError):
        Cluster(id="c", datacenter_id="d", name=" ", node_count=0)
    with pytest.raises(ValueError):
        TopologyNode(node_id=" ", hostname="h", status="online", version="1")
    with pytest.raises(ValueError):
        TopologyNode(node_id="n", hostname=" ", status="online", version="1")
    with pytest.raises(ValueError):
        TopologyNode(node_id="n", hostname="h", status="online", version=" ")
    with pytest.raises(ValueError):
        TopologyEdge(source_id=" ", target_id="b", relation="HOSTS")
    with pytest.raises(ValueError):
        TopologyEdge(source_id="a", target_id=" ", relation="HOSTS")
    with pytest.raises(ValueError):
        TopologyEdge(source_id="a", target_id="b", relation="HOSTS", weight=-1)
    # missing cluster on node
    with pytest.raises(ValueError):
        TopologyGraph(
            regions=(Region(id="r", name="R", country="C"),),
            datacenters=(
                Datacenter(id="d", region_id="r", name="D", capacity=1),
            ),
            clusters=(
                Cluster(id="c", datacenter_id="d", name="C", node_count=0),
            ),
            nodes=(
                TopologyNode(
                    node_id="n",
                    hostname="h",
                    status="online",
                    version="1",
                    cluster_id="missing",
                ),
            ),
            edges=(),
        )
    assert cluster_health(
        TopologyGraph(
            regions=(),
            datacenters=(),
            clusters=(),
            nodes=(),
            edges=(),
        ),
        "nope",
    ) is None
    assert region_summary(
        TopologyGraph(
            regions=(),
            datacenters=(),
            clusters=(),
            nodes=(),
            edges=(),
        ),
        "nope",
    ) is None
    # empty cluster health
    g = TopologyGraph(
        regions=(Region(id="r", name="R", country="C"),),
        datacenters=(Datacenter(id="d", region_id="r", name="D", capacity=0),),
        clusters=(Cluster(id="c", datacenter_id="d", name="Empty", node_count=0),),
        nodes=(),
        edges=(),
    )
    h = cluster_health(g, "c")
    assert h is not None and h.status == "empty"
