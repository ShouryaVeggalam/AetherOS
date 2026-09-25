"""Workload graph — static edges from workloads to resource demands.

Complements the orchestrator catalog with cognitive graph seeds.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.knowledge.resource_types import RelationKind, ResourceKind


@dataclass(frozen=True, slots=True)
class WorkloadEdge:
    """Directed relation from a workload concept to a resource kind.

    Attributes:
        workload_id: Ontology workload concept id.
        relation: Graph relation (typically USES or CAUSES).
        resource: Target resource kind.
        intensity: Relative demand weight 0.0–1.0.
        note: Public systems note (never personal content).
    """

    workload_id: str
    relation: RelationKind
    resource: ResourceKind
    intensity: float
    note: str

    def __post_init__(self) -> None:
        """Validate intensity bounds."""

        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("intensity must be between 0 and 1")


WORKLOAD_EDGES: tuple[WorkloadEdge, ...] = (
    WorkloadEdge(
        "workload.coding",
        "CAUSES",
        "cpu",
        0.75,
        "Coding usually increases CPU after IDE / Cursor activity.",
    ),
    WorkloadEdge(
        "workload.coding",
        "USES",
        "memory",
        0.45,
        "Language servers and indexes consume memory.",
    ),
    WorkloadEdge(
        "workload.rendering",
        "CAUSES",
        "disk",
        0.85,
        "Video rendering creates sustained disk activity.",
    ),
    WorkloadEdge(
        "workload.rendering",
        "USES",
        "cpu",
        0.9,
        "Encode pipelines are CPU heavy.",
    ),
    WorkloadEdge(
        "workload.gaming",
        "CAUSES",
        "cpu",
        0.7,
        "Gaming increases foreground utilization.",
    ),
    WorkloadEdge(
        "workload.gaming",
        "USES",
        "gpu",
        0.95,
        "Games depend on GPU availability.",
    ),
    WorkloadEdge(
        "process.cursor",
        "PREDICTS",
        "cpu",
        0.65,
        "Cursor launch often predicts a near-term CPU rise.",
    ),
    WorkloadEdge(
        "process.browser",
        "CAUSES",
        "cpu",
        0.55,
        "Browser rendering can cause CPU spikes.",
    ),
)


def edges_for_workload(workload_id: str) -> tuple[WorkloadEdge, ...]:
    """Return edges seeded from one workload / process concept."""

    return tuple(e for e in WORKLOAD_EDGES if e.workload_id == workload_id)
