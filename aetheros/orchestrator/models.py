"""Resource Orchestrator data contracts for AetherOS v1.5.

Immutable planning objects only. Recommendation-only — never executes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aetheros.cluster.models import NodeHealth

DemandLevel = Literal["high", "medium", "low", "none"]
WorkloadName = Literal[
    "Python Development",
    "AI Training",
    "Video Rendering",
    "Gaming",
    "Data Analysis",
    "Balanced",
]


@dataclass(frozen=True, slots=True)
class WorkloadProfile:
    """Resource demand profile for one workload type.

    Attributes:
        name: Canonical workload name.
        cpu: CPU demand level.
        memory: Memory demand level.
        disk: Disk demand level.
        gpu: GPU demand level.
        latency: Latency sensitivity (high = needs low latency).
        description: Short operator-facing summary.
    """

    name: WorkloadName
    cpu: DemandLevel
    memory: DemandLevel
    disk: DemandLevel
    gpu: DemandLevel
    latency: DemandLevel
    description: str


@dataclass(frozen=True, slots=True)
class CandidateNode:
    """Orchestrator view of a cluster node for planning.

    Attributes:
        node_id: Stable cluster node id.
        hostname: Display hostname.
        cpu: Current CPU percent (load).
        memory: Current memory percent (load).
        disk: Current disk percent (used).
        battery: Battery percent, or None if N/A / plugged desktop.
        gpu: GPU availability score 0–100 (100 = strong GPU present).
        network_latency: Transport latency in milliseconds.
        platform: OS platform string.
        health: healthy / warning / critical / offline.
    """

    node_id: str
    hostname: str
    cpu: float
    memory: float
    disk: float
    battery: float | None
    gpu: float
    network_latency: float
    platform: str
    health: NodeHealth


@dataclass(frozen=True, slots=True)
class ConstraintFailure:
    """One immutable reason a node was rejected by constraints."""

    node_id: str
    hostname: str
    reason: str


@dataclass(frozen=True, slots=True)
class NodeScore:
    """Suitability score for one eligible node.

    Attributes:
        node: Candidate that passed constraints.
        score: Suitability 0–100.
        breakdown: Human-readable metric contributions.
    """

    node: CandidateNode
    score: int
    breakdown: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate score bounds."""

        if not 0 <= self.score <= 100:
            raise ValueError("score must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """Immutable recommendation plan for a workload.

    Attributes:
        workload: Selected workload profile.
        recommended_node: Best eligible node, or None.
        score: Suitability of the recommended node (0 if none).
        rejected_nodes: Constraint failures.
        ranked: All scored eligible nodes (best first).
        explanation: Evidence-based explanation text lines.
        status: Always recommendation-only messaging.
    """

    workload: WorkloadProfile
    recommended_node: CandidateNode | None
    score: int
    rejected_nodes: tuple[ConstraintFailure, ...]
    ranked: tuple[NodeScore, ...]
    explanation: tuple[str, ...]
    status: str = "Recommendation only — no execution performed."
