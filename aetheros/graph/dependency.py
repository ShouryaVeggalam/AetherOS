"""Dependency edges — how services and infrastructure rely on each other.

Declarative catalog for cascade simulation. Never mutates live deps.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

DependencyKind = Literal["REQUIRES", "BACKS", "FEEDS", "SHARES"]


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    """One immutable dependency relation.

    Attributes:
        source_id: Dependent entity.
        target_id: Dependency target.
        kind: Relation class.
        weight: Coupling strength 0–1 (higher = stronger cascade).
        note: Public systems note.
    """

    source_id: str
    target_id: str
    kind: DependencyKind
    weight: float
    note: str

    def __post_init__(self) -> None:
        """Validate weight."""

        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("weight must be in [0, 1]")


SEED_DEPENDENCIES: tuple[DependencyEdge, ...] = (
    DependencyEdge(
        "svc.api",
        "svc.cache",
        "REQUIRES",
        0.8,
        "API gateway requires cache for low-latency reads.",
    ),
    DependencyEdge(
        "svc.api",
        "svc.db",
        "REQUIRES",
        0.95,
        "API gateway requires primary database availability.",
    ),
    DependencyEdge(
        "svc.compile",
        "svc.cache",
        "REQUIRES",
        0.7,
        "Compile workers use cache to avoid repeated fetches.",
    ),
    DependencyEdge(
        "svc.index",
        "svc.db",
        "FEEDS",
        0.6,
        "Indexer feeds metadata into the primary database.",
    ),
    DependencyEdge(
        "svc.batch",
        "svc.db",
        "REQUIRES",
        0.5,
        "Batch jobs require database for checkpoints.",
    ),
    DependencyEdge(
        "node.local.1",
        "cluster.local",
        "BACKS",
        0.9,
        "Local node backs the local cluster capacity.",
    ),
    DependencyEdge(
        "cluster.local",
        "dc.local",
        "BACKS",
        0.85,
        "Cluster capacity backs datacenter headroom.",
    ),
    DependencyEdge(
        "dc.local",
        "region.local",
        "BACKS",
        0.8,
        "Datacenter pressure propagates to regional latency.",
    ),
    DependencyEdge(
        "svc.edge",
        "region.edge",
        "SHARES",
        0.55,
        "Edge gateway shares regional network path.",
    ),
    DependencyEdge(
        "svc.api",
        "node.local.1",
        "REQUIRES",
        0.75,
        "API processes run on the local compute node.",
    ),
)
