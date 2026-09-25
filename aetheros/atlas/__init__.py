"""Atlas — global infrastructure reasoning (v5 compatibility facade).

Atlas was specified as World → Regions → Datacenters → Clusters → Nodes
with Digital Twin. In this codebase those capabilities live in Horizon
and Twin; Atlas re-exports them under the historical generation name
without circular imports or duplicated logic.
"""

from __future__ import annotations

from aetheros.horizon import (
    DEFAULT_CENSUS,
    HorizonReport,
    HorizonRuntime,
    PlanetaryCensus,
    WorldGraph,
    WorldGraphSnapshot,
)
from aetheros.horizon.geography import SEED_REGIONS, GeoPoint, GeoRegion, haversine_km
from aetheros.horizon.topology import TopologyEdge, TopologyNode, build_sample_topology
from aetheros.twin import GlobalTwin, GlobalTwinReport

__all__ = [
    "DEFAULT_CENSUS",
    "GeoPoint",
    "GeoRegion",
    "GlobalTwin",
    "GlobalTwinReport",
    "HorizonReport",
    "HorizonRuntime",
    "PlanetaryCensus",
    "SEED_REGIONS",
    "TopologyEdge",
    "TopologyNode",
    "WorldGraph",
    "WorldGraphSnapshot",
    "build_sample_topology",
    "haversine_km",
]
