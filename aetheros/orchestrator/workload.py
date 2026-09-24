"""Workload catalog for the Resource Orchestrator.

Each workload declares demand levels only — never triggers execution.
"""

from __future__ import annotations

from aetheros.orchestrator.models import WorkloadName, WorkloadProfile

_WORKLOADS: tuple[WorkloadProfile, ...] = (
    WorkloadProfile(
        name="Python Development",
        cpu="medium",
        memory="medium",
        disk="low",
        gpu="low",
        latency="high",
        description="Interactive coding with low-latency preference.",
    ),
    WorkloadProfile(
        name="AI Training",
        cpu="high",
        memory="high",
        disk="medium",
        gpu="high",
        latency="low",
        description="Heavy compute and GPU for model training.",
    ),
    WorkloadProfile(
        name="Video Rendering",
        cpu="high",
        memory="medium",
        disk="high",
        gpu="medium",
        latency="low",
        description="CPU/disk intensive media export.",
    ),
    WorkloadProfile(
        name="Gaming",
        cpu="high",
        memory="medium",
        disk="low",
        gpu="high",
        latency="high",
        description="Interactive GPU workload with low latency.",
    ),
    WorkloadProfile(
        name="Data Analysis",
        cpu="medium",
        memory="high",
        disk="medium",
        gpu="low",
        latency="low",
        description="Memory-heavy analytics jobs.",
    ),
    WorkloadProfile(
        name="Balanced",
        cpu="medium",
        memory="medium",
        disk="medium",
        gpu="medium",
        latency="medium",
        description="General-purpose balanced placement.",
    ),
)

_BY_NAME: dict[str, WorkloadProfile] = {w.name: w for w in _WORKLOADS}


def all_workloads() -> tuple[WorkloadProfile, ...]:
    """Return the full immutable workload catalog."""

    return _WORKLOADS


def get_workload(name: WorkloadName | str) -> WorkloadProfile:
    """Look up a workload by name.

    Raises:
        KeyError: When the name is not in the catalog.
    """

    if name not in _BY_NAME:
        raise KeyError(f"Unknown workload: {name}")
    return _BY_NAME[name]


def workload_names() -> tuple[WorkloadName, ...]:
    """Return ordered workload names for UI cycling."""

    return tuple(w.name for w in _WORKLOADS)


def next_workload(current: WorkloadName | str) -> WorkloadProfile:
    """Cycle to the next workload in the catalog."""

    names = workload_names()
    if current not in names:
        return _WORKLOADS[0]
    index = names.index(current)  # type: ignore[arg-type]
    return _WORKLOADS[(index + 1) % len(_WORKLOADS)]
