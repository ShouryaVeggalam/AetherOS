"""Demo topology metadata aligned with Federation demo node regions.

Only describes regions that federation demo nodes actually report
(local, us-west, eu-central). Never invents unaffiliated geography.
"""

from __future__ import annotations

from aetheros.topology.builder import NodePlacement, TopologyMetadata
from aetheros.topology.models import Cluster, Datacenter, Region


def demo_topology_metadata() -> TopologyMetadata:
    """Catalog matching `seed_demo_federation` node regions."""

    regions = {
        "local": Region(
            id="local",
            name="Local",
            country="Local",
            metadata={"tier": "edge"},
        ),
        "us-west": Region(
            id="us-west",
            name="US West",
            country="United States",
            metadata={"continent": "Americas"},
        ),
        "eu-central": Region(
            id="eu-central",
            name="Europe Central",
            country="Germany",
            metadata={"continent": "Europe"},
        ),
    }
    datacenters = (
        Datacenter(
            id="dc-local-lab",
            region_id="local",
            name="Local Lab DC",
            capacity=8,
        ),
        Datacenter(
            id="dc-sfo",
            region_id="us-west",
            name="San Francisco DC",
            capacity=64,
        ),
        Datacenter(
            id="dc-fra",
            region_id="eu-central",
            name="Frankfurt DC",
            capacity=48,
        ),
    )
    clusters = (
        Cluster(
            id="cluster-alpha",
            datacenter_id="dc-local-lab",
            name="Cluster Alpha",
            node_count=0,
        ),
        Cluster(
            id="cluster-beta",
            datacenter_id="dc-sfo",
            name="Cluster Beta",
            node_count=0,
        ),
        Cluster(
            id="cluster-gamma",
            datacenter_id="dc-fra",
            name="Cluster Gamma",
            node_count=0,
        ),
    )
    placements = (
        NodePlacement(
            node_id="node-local",
            cluster_id="cluster-alpha",
            datacenter_id="dc-local-lab",
        ),
        NodePlacement(
            node_id="node-peer-a",
            cluster_id="cluster-beta",
            datacenter_id="dc-sfo",
        ),
        NodePlacement(
            node_id="node-peer-b",
            cluster_id="cluster-gamma",
            datacenter_id="dc-fra",
        ),
    )
    return TopologyMetadata(
        regions=regions,
        datacenters=datacenters,
        clusters=clusters,
        placements=placements,
        peer_links=(("node-local", "node-peer-a"),),
        replicate_links=(("cluster-beta", "cluster-gamma"),),
    )
