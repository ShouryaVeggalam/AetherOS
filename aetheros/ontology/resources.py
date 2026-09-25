"""Ontology resources — computing resource entities for Genesis.

Immutable catalog only. Never probes or allocates hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ResourceEntity = Literal[
    "cpu",
    "gpu",
    "memory",
    "disk",
    "network",
    "cache",
]


@dataclass(frozen=True, slots=True)
class ResourceConcept:
    """One resource entity in the Genesis ontology.

    Attributes:
        entity_id: Stable id (e.g. ``resource.cpu``).
        kind: Resource class.
        label: Display name.
        unit: Measurement unit.
        summary: Public systems description.
    """

    entity_id: str
    kind: ResourceEntity
    label: str
    unit: str
    summary: str


RESOURCE_ENTITIES: tuple[ResourceConcept, ...] = (
    ResourceConcept(
        "resource.cpu",
        "cpu",
        "CPU",
        "percent",
        "Processor capacity and scheduling latency.",
    ),
    ResourceConcept(
        "resource.gpu",
        "gpu",
        "GPU",
        "percent",
        "Accelerator throughput for training and rendering.",
    ),
    ResourceConcept(
        "resource.memory",
        "memory",
        "Memory",
        "percent",
        "Working-set RAM pressure and reclaim behavior.",
    ),
    ResourceConcept(
        "resource.disk",
        "disk",
        "Disk",
        "percent",
        "Persistent storage capacity and I/O contention.",
    ),
    ResourceConcept(
        "resource.network",
        "network",
        "Network",
        "ms",
        "Inter-node and edge communication latency.",
    ),
    ResourceConcept(
        "resource.cache",
        "cache",
        "Cache",
        "MB",
        "Local cache allocation affecting compile and fetch latency.",
    ),
)
