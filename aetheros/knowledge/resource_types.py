"""Resource type catalog for Cognitive Operating Intelligence.

Pure declarative types — no telemetry collection, no OS mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ResourceKind = Literal[
    "cpu",
    "memory",
    "disk",
    "network",
    "gpu",
    "battery",
    "process",
    "intent",
    "cluster_node",
    "simulation",
]

RelationKind = Literal[
    "CAUSES",
    "USES",
    "DEPENDS_ON",
    "PREDICTS",
    "EXPLAINS",
]


@dataclass(frozen=True, slots=True)
class ResourceType:
    """One canonical resource kind in the AetherOS ontology.

    Attributes:
        kind: Machine-stable resource key.
        label: Operator-facing name.
        unit: Measurement unit (percent, ms, boolean, …).
        description: Short systems meaning.
    """

    kind: ResourceKind
    label: str
    unit: str
    description: str


RESOURCE_TYPES: tuple[ResourceType, ...] = (
    ResourceType("cpu", "CPU", "percent", "Processor utilization."),
    ResourceType("memory", "Memory", "percent", "RAM pressure."),
    ResourceType(
        "disk", "Disk", "percent", "Storage utilization / IO intensity proxy."
    ),
    ResourceType("network", "Network", "ms", "Latency / bandwidth pressure proxy."),
    ResourceType("gpu", "GPU", "score", "Accelerator availability score 0–100."),
    ResourceType(
        "battery", "Battery", "percent", "Charge remaining on portable hosts."
    ),
    ResourceType("process", "Process", "name", "Userspace process / workload actor."),
    ResourceType("intent", "Intent", "profile", "Operator intent profile."),
    ResourceType(
        "cluster_node",
        "Cluster Node",
        "host",
        "Member of the multi-device cluster.",
    ),
    ResourceType(
        "simulation",
        "Simulation",
        "score",
        "What-if simulation outcome (never executed).",
    ),
)


def get_resource_type(kind: ResourceKind | str) -> ResourceType:
    """Look up a resource type by kind."""

    for item in RESOURCE_TYPES:
        if item.kind == kind:
            return item
    raise KeyError(f"Unknown resource kind: {kind}")
