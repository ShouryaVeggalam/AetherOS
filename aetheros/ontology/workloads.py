"""Ontology workloads — workload classes Genesis can hypothesize about."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WorkloadConcept:
    """One workload entity in the Genesis ontology."""

    entity_id: str
    label: str
    summary: str
    primary_resources: tuple[str, ...]


WORKLOAD_ENTITIES: tuple[WorkloadConcept, ...] = (
    WorkloadConcept(
        "workload.interactive_coding",
        "Interactive Coding",
        "Editor/compile loops sensitive to CPU latency before memory pressure.",
        ("resource.cpu", "resource.cache", "resource.memory"),
    ),
    WorkloadConcept(
        "workload.compile",
        "Compilation",
        "Build/compile jobs that benefit from cache allocation.",
        ("resource.cpu", "resource.cache", "resource.disk"),
    ),
    WorkloadConcept(
        "workload.training",
        "AI Training",
        "Sustained GPU/CPU training with memory and network fan-in.",
        ("resource.gpu", "resource.memory", "resource.network"),
    ),
    WorkloadConcept(
        "workload.rendering",
        "Video Rendering",
        "Long-running encode/export with disk and CPU pressure.",
        ("resource.cpu", "resource.disk", "resource.gpu"),
    ),
    WorkloadConcept(
        "workload.serving",
        "Online Serving",
        "Latency-sensitive request paths across cluster nodes.",
        ("resource.cpu", "resource.network", "resource.memory"),
    ),
)
