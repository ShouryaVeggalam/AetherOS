"""Atlas — v4.0 P5 Distributed Observatory (presentation layer).

Also re-exports the historical v5 Horizon/Twin facade for compatibility.
Atlas Dashboard is Rich-only, read-only, and never mutates engines.
"""

from __future__ import annotations

from aetheros.atlas.app import main, render_app, run
from aetheros.atlas.demo import build_demo_snapshot
from aetheros.atlas.router import (
    HOTKEYS,
    PAGE_IDS,
    PAGE_TITLES,
    AtlasRouter,
    normalize_page,
)
from aetheros.atlas.snapshot import AtlasSnapshot, HealthSignal
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
    "AtlasRouter",
    "AtlasSnapshot",
    "DEFAULT_CENSUS",
    "GeoPoint",
    "GeoRegion",
    "GlobalTwin",
    "GlobalTwinReport",
    "HOTKEYS",
    "HealthSignal",
    "HorizonReport",
    "HorizonRuntime",
    "PAGE_IDS",
    "PAGE_TITLES",
    "PlanetaryCensus",
    "SEED_REGIONS",
    "TopologyEdge",
    "TopologyNode",
    "WorldGraph",
    "WorldGraphSnapshot",
    "build_demo_snapshot",
    "build_sample_topology",
    "haversine_km",
    "main",
    "normalize_page",
    "render_app",
    "run",
]
