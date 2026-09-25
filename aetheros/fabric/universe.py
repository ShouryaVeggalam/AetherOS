"""Fabric universe — planetary-scale census for the Aether Fabric.

Census aggregates are simulation catalog values for the dashboard.
A smaller sample set backs the navigable graph.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UniverseCensus:
    """Immutable planetary fabric census.

    Attributes match the Fabric dashboard example.
    """

    connected_nodes: int
    regions: int
    datacenters: int
    clusters: int
    synchronization: float
    global_health: float

    def __post_init__(self) -> None:
        """Validate percentages."""

        if not 0.0 <= self.synchronization <= 100.0:
            raise ValueError("synchronization must be in [0, 100]")
        if not 0.0 <= self.global_health <= 100.0:
            raise ValueError("global_health must be in [0, 100]")


DEFAULT_UNIVERSE = UniverseCensus(
    connected_nodes=241_880,
    regions=47,
    datacenters=322,
    clusters=2_913,
    synchronization=99.98,
    global_health=98.7,
)
