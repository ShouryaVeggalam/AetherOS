"""Geographic primitives for planetary topology.

Pure math only — never probes the network or GPS hardware.
Coordinates are approximate public catalog values for simulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

NetworkClass = Literal["fiber", "satellite", "cellular", "wifi", "mesh"]


@dataclass(frozen=True, slots=True)
class GeoPoint:
    """One WGS-84 coordinate.

    Attributes:
        latitude: Degrees north (−90…90).
        longitude: Degrees east (−180…180).
        label: Optional human label.
    """

    latitude: float
    longitude: float
    label: str = ""

    def __post_init__(self) -> None:
        """Validate coordinate ranges."""

        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude out of range")
        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError("longitude out of range")


@dataclass(frozen=True, slots=True)
class GeoRegion:
    """Named planetary region with a centroid.

    Attributes:
        region_id: Stable id (e.g. ``region.eu``).
        name: Display name.
        centroid: Approximate center.
        countries: ISO-ish country codes hosted in this region.
    """

    region_id: str
    name: str
    centroid: GeoPoint
    countries: tuple[str, ...]


def haversine_km(a: GeoPoint, b: GeoPoint) -> float:
    """Great-circle distance in kilometres between two points."""

    r_earth = 6371.0
    lat1, lat2 = math.radians(a.latitude), math.radians(b.latitude)
    dlat = math.radians(b.latitude - a.latitude)
    dlon = math.radians(b.longitude - a.longitude)
    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * r_earth * math.asin(min(1.0, math.sqrt(h)))


# Seeded public regions for Horizon simulations (not live inventory).
SEED_REGIONS: tuple[GeoRegion, ...] = (
    GeoRegion(
        "region.na",
        "North America",
        GeoPoint(39.8, -98.5, "NA"),
        ("US", "CA", "MX"),
    ),
    GeoRegion(
        "region.eu",
        "Europe",
        GeoPoint(50.0, 10.0, "EU"),
        ("DE", "FR", "GB", "NL", "SE"),
    ),
    GeoRegion(
        "region.apac",
        "Asia Pacific",
        GeoPoint(22.3, 114.2, "APAC"),
        ("JP", "SG", "AU", "IN", "KR"),
    ),
    GeoRegion(
        "region.sa",
        "South America",
        GeoPoint(-14.2, -51.9, "SA"),
        ("BR", "CL", "AR"),
    ),
    GeoRegion(
        "region.mea",
        "Middle East & Africa",
        GeoPoint(25.2, 55.3, "MEA"),
        ("AE", "ZA", "EG"),
    ),
    GeoRegion(
        "region.arctic",
        "Arctic Edge",
        GeoPoint(78.2, 15.6, "ARC"),
        ("SJ",),
    ),
)
