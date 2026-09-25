"""Service catalog — logical services Sentinel can reason about.

Inventory only. Never starts, stops, or restarts services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ServiceTier = Literal["critical", "interactive", "background", "batch"]


@dataclass(frozen=True, slots=True)
class ServiceNode:
    """One immutable logical service.

    Attributes:
        service_id: Stable id.
        name: Display name.
        tier: Criticality class.
        region_id: Hosting region label.
        load: Normalized load 0–100.
        health: Health fraction 0–1.
    """

    service_id: str
    name: str
    tier: ServiceTier
    region_id: str
    load: float
    health: float

    def __post_init__(self) -> None:
        """Validate load and health."""

        if not 0.0 <= self.load <= 100.0:
            raise ValueError("load must be in [0, 100]")
        if not 0.0 <= self.health <= 1.0:
            raise ValueError("health must be in [0, 1]")


SEED_SERVICES: tuple[ServiceNode, ...] = (
    ServiceNode("svc.api", "API Gateway", "critical", "region.local", 55.0, 0.98),
    ServiceNode("svc.db", "Primary Database", "critical", "region.local", 48.0, 0.97),
    ServiceNode("svc.cache", "Cache Tier", "interactive", "region.local", 40.0, 0.99),
    ServiceNode(
        "svc.index", "Background Indexer", "background", "region.local", 70.0, 0.94
    ),
    ServiceNode(
        "svc.compile", "Compile Workers", "interactive", "region.local", 65.0, 0.95
    ),
    ServiceNode("svc.batch", "Batch Jobs", "batch", "region.local", 35.0, 0.96),
    ServiceNode("svc.edge", "Edge Gateway", "interactive", "region.edge", 42.0, 0.93),
)
