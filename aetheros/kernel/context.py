"""Userspace Kernel Intelligence — resource context (NOT an OS kernel).

This package provides a read-only resource/context graph for planners.
It never loads kernel modules, never calls sudo, and never mutates
kernel state. The name follows the AetherOS generation map (v2), not
the Linux kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aetheros.knowledge.resource_types import RESOURCE_TYPES, ResourceType
from aetheros.knowledge.workload_graph import WORKLOAD_EDGES, WorkloadEdge
from aetheros.ontology import RESOURCE_ENTITIES, SEED_RELATIONS, ResourceConcept

ContextKind = Literal["cpu", "memory", "disk", "network", "gpu", "process"]


@dataclass(frozen=True, slots=True)
class ResourceContext:
    """Immutable snapshot of userspace resource context catalog."""

    resources: tuple[ResourceType, ...]
    ontology_resources: tuple[ResourceConcept, ...]
    workload_edges: tuple[WorkloadEdge, ...]
    relation_count: int
    status: str = "userspace-only"


@dataclass
class KernelIntelligence:
    """Read-only resource context facade (userspace).

    Attributes:
        label: Display name clarifying non-kernel nature.
    """

    label: str = "Userspace Kernel Intelligence"

    def context(self) -> ResourceContext:
        """Return the combined resource/workload context catalog."""

        return ResourceContext(
            resources=RESOURCE_TYPES,
            ontology_resources=RESOURCE_ENTITIES,
            workload_edges=WORKLOAD_EDGES,
            relation_count=len(SEED_RELATIONS),
        )
