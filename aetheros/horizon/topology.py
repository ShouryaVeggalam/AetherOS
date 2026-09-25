"""Planetary topology catalog — immutable nodes and census aggregates.

Separates a navigable sample hierarchy (for graph algorithms) from
planetary-scale census counts (for dashboard / capacity forecasts).
Nothing here contacts live infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aetheros.horizon.geography import SEED_REGIONS, GeoPoint

NodeKind = Literal[
    "earth",
    "region",
    "country",
    "datacenter",
    "cluster",
    "node",
    "process",
    "edge_gateway",
    "sensor",
    "mobile",
    "iot",
    "robot",
    "satellite",
    "hpc",
]

HierarchyLevel = Literal[
    "earth",
    "region",
    "country",
    "datacenter",
    "cluster",
    "node",
    "process",
]


@dataclass(frozen=True, slots=True)
class TopologyNode:
    """One immutable entity in the planetary topology.

    Attributes:
        node_id: Globally unique id.
        kind: Entity class.
        name: Human label.
        parent_id: Parent in the hierarchy, or None for Earth.
        location: Optional geo anchor.
        capacity_score: Relative compute capacity 0–100.
        health: Health fraction 0–1.
        metadata: Public systems tags only.
    """

    node_id: str
    kind: NodeKind
    name: str
    parent_id: str | None
    location: GeoPoint | None
    capacity_score: float
    health: float
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Clamp health and capacity."""

        if not 0.0 <= self.health <= 1.0:
            raise ValueError("health must be in [0, 1]")
        if not 0.0 <= self.capacity_score <= 100.0:
            raise ValueError("capacity_score must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class TopologyEdge:
    """Directed containment or communication relation."""

    source_id: str
    target_id: str
    relation: Literal["CONTAINS", "CONNECTS", "SENSES", "ORBITS"]
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class PlanetaryCensus:
    """Planetary-scale aggregate counts (simulation catalog).

    Attributes mirror the Horizon dashboard summary. Values are seeded
    public estimates for what-if reasoning — not live probes.
    """

    regions: int
    countries: int
    datacenters: int
    clusters: int
    nodes: int
    processes: int
    edge_devices: int
    robots: int
    satellites: int
    hpc_clusters: int
    world_health: float

    def __post_init__(self) -> None:
        """Validate health."""

        if not 0.0 <= self.world_health <= 100.0:
            raise ValueError("world_health must be in [0, 100]")


# Dashboard-scale census used in Horizon examples.
DEFAULT_CENSUS = PlanetaryCensus(
    regions=42,
    countries=118,
    datacenters=318,
    clusters=2481,
    nodes=184_220,
    processes=4_820_000,
    edge_devices=52_400,
    robots=1_240,
    satellites=86,
    hpc_clusters=64,
    world_health=99.1,
)


def build_sample_topology() -> (
    tuple[tuple[TopologyNode, ...], tuple[TopologyEdge, ...]]
):
    """Construct a compact navigable sample of the planetary hierarchy.

    Returns a small NetworkX-ready graph representing Earth → regions →
    sample countries / DCs / clusters / nodes / edge / robotics / satellites.
    """

    nodes: list[TopologyNode] = [
        TopologyNode(
            "earth",
            "earth",
            "Earth",
            None,
            GeoPoint(0.0, 0.0, "Earth"),
            100.0,
            0.991,
            (("scope", "planetary"),),
        )
    ]
    edges: list[TopologyEdge] = []

    for region in SEED_REGIONS:
        nodes.append(
            TopologyNode(
                region.region_id,
                "region",
                region.name,
                "earth",
                region.centroid,
                80.0,
                0.985,
                (("countries", ",".join(region.countries)),),
            )
        )
        edges.append(TopologyEdge("earth", region.region_id, "CONTAINS", 1.0))
        for index, country in enumerate(region.countries[:2]):
            country_id = f"country.{country.lower()}"
            nodes.append(
                TopologyNode(
                    country_id,
                    "country",
                    country,
                    region.region_id,
                    region.centroid,
                    70.0,
                    0.98,
                )
            )
            edges.append(TopologyEdge(region.region_id, country_id, "CONTAINS", 1.0))
            dc_id = f"dc.{country.lower()}.1"
            nodes.append(
                TopologyNode(
                    dc_id,
                    "datacenter",
                    f"{country}-DC1",
                    country_id,
                    region.centroid,
                    75.0,
                    0.99,
                    (("tier", "3"),),
                )
            )
            edges.append(TopologyEdge(country_id, dc_id, "CONTAINS", 1.0))
            cluster_id = f"cluster.{country.lower()}.a"
            nodes.append(
                TopologyNode(
                    cluster_id,
                    "cluster",
                    f"{country}-Cluster-A",
                    dc_id,
                    region.centroid,
                    65.0,
                    0.988,
                )
            )
            edges.append(TopologyEdge(dc_id, cluster_id, "CONTAINS", 1.0))
            node_id = f"node.{country.lower()}.1"
            nodes.append(
                TopologyNode(
                    node_id,
                    "node",
                    f"{country}-node-1",
                    cluster_id,
                    region.centroid,
                    55.0,
                    0.995,
                    (("role", "compute"),),
                )
            )
            edges.append(TopologyEdge(cluster_id, node_id, "CONTAINS", 1.0))
            proc_id = f"process.{country.lower()}.init"
            nodes.append(
                TopologyNode(
                    proc_id,
                    "process",
                    "init",
                    node_id,
                    None,
                    10.0,
                    1.0,
                )
            )
            edges.append(TopologyEdge(node_id, proc_id, "CONTAINS", 1.0))
            if index == 0:
                # Attach one edge gateway + IoT + robot + optional satellite per region.
                gw_id = f"edge.gw.{country.lower()}"
                nodes.append(
                    TopologyNode(
                        gw_id,
                        "edge_gateway",
                        f"{country}-Gateway",
                        region.region_id,
                        region.centroid,
                        40.0,
                        0.97,
                        (("network", "fiber"),),
                    )
                )
                edges.append(TopologyEdge(region.region_id, gw_id, "CONNECTS", 0.8))
                sensor_id = f"sensor.{country.lower()}.1"
                nodes.append(
                    TopologyNode(
                        sensor_id,
                        "sensor",
                        f"{country}-Temp-1",
                        gw_id,
                        region.centroid,
                        5.0,
                        0.96,
                        (("kind", "temperature"),),
                    )
                )
                edges.append(TopologyEdge(gw_id, sensor_id, "SENSES", 0.5))
                robot_id = f"robot.{country.lower()}.1"
                nodes.append(
                    TopologyNode(
                        robot_id,
                        "robot",
                        f"{country}-Bot-1",
                        region.region_id,
                        region.centroid,
                        30.0,
                        0.94,
                        (("autonomy", "supervised"),),
                    )
                )
                edges.append(TopologyEdge(region.region_id, robot_id, "CONTAINS", 0.6))

        if region.region_id == "region.apac":
            sat_id = "satellite.leo.1"
            nodes.append(
                TopologyNode(
                    sat_id,
                    "satellite",
                    "LEO-Relay-1",
                    "earth",
                    GeoPoint(0.0, 140.0, "LEO"),
                    50.0,
                    0.99,
                    (("orbit", "LEO"),),
                )
            )
            edges.append(TopologyEdge("earth", sat_id, "ORBITS", 0.7))
            hpc_id = "hpc.apac.1"
            nodes.append(
                TopologyNode(
                    hpc_id,
                    "hpc",
                    "APAC-HPC-1",
                    "region.apac",
                    region.centroid,
                    95.0,
                    0.992,
                    (("gpus", "4096"),),
                )
            )
            edges.append(TopologyEdge("region.apac", hpc_id, "CONTAINS", 1.0))

    return tuple(nodes), tuple(edges)
