"""Distributed Scheduler models — simulation-only placement contracts.

v4.0 P3. Plans and scores are recommendations. Never executes workloads,
SSH, Kubernetes, or Docker APIs. Digital Twin evaluation only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

ConstraintKind = Literal[
    "MAX_CPU",
    "MAX_MEMORY",
    "REQUIRE_GPU",
    "REGION_LOCK",
    "AVOID_OVERLOAD",
]


@dataclass(frozen=True, slots=True)
class Workload:
    """Immutable workload request for simulated placement."""

    id: str
    name: str
    cpu_request: float
    memory_request: float
    gpu_request: float
    priority: float

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        for name in ("cpu_request", "memory_request", "gpu_request"):
            value = float(getattr(self, name))
            if value < 0.0:
                raise ValueError(f"{name} must be >= 0")
        if not 0.0 <= self.priority <= 100.0:
            raise ValueError("priority must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class NodeCapacity:
    """Observed / derived capacity of one candidate node."""

    node_id: str
    available_cpu: float
    available_memory: float
    available_gpu: float
    utilization: float
    latency_ms: float = 5.0
    region_id: str = ""
    cluster_health: float = 70.0
    hostname: str = ""

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id must be non-empty")
        for name in (
            "available_cpu",
            "available_memory",
            "available_gpu",
            "utilization",
            "cluster_health",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be in [0, 100]")
        if self.latency_ms < 0.0:
            raise ValueError("latency_ms must be >= 0")


@dataclass(frozen=True, slots=True)
class ScheduleConstraint:
    """One hard constraint applied before scoring."""

    kind: ConstraintKind
    value: float | str = 0.0

    def __post_init__(self) -> None:
        if self.kind not in (
            "MAX_CPU",
            "MAX_MEMORY",
            "REQUIRE_GPU",
            "REGION_LOCK",
            "AVOID_OVERLOAD",
        ):
            raise ValueError(f"invalid constraint kind: {self.kind}")


@dataclass(frozen=True, slots=True)
class SchedulePlan:
    """One ranked candidate placement (recommendation only)."""

    workload: Workload
    target_node: str
    score: float
    reasoning: str
    predicted_cpu: float = 0.0
    predicted_memory: float = 0.0
    predicted_latency_ms: float = 0.0

    def __post_init__(self) -> None:
        if not self.target_node.strip():
            raise ValueError("target_node must be non-empty")
        if not 0.0 <= self.score <= 100.0:
            raise ValueError("score must be in [0, 100]")
        if not self.reasoning.strip():
            raise ValueError("reasoning must be non-empty")


@dataclass(frozen=True, slots=True)
class TradeOff:
    """Explainable trade-off between the best plan and an alternative."""

    versus_node: str
    summary: str
    score_delta: float

    def __post_init__(self) -> None:
        if not self.versus_node.strip():
            raise ValueError("versus_node must be non-empty")
        if not self.summary.strip():
            raise ValueError("summary must be non-empty")


@dataclass(frozen=True, slots=True)
class ScheduleResult:
    """Immutable scheduler output — simulation recommendations only."""

    plans: tuple[SchedulePlan, ...]
    cluster_health: float
    predicted_latency: float
    confidence: float
    best_plan: SchedulePlan | None = None
    trade_offs: tuple[TradeOff, ...] = ()
    rejected: tuple[tuple[str, str], ...] = ()
    created_at: datetime | None = None
    status: Literal["simulation_only"] = "simulation_only"

    def __post_init__(self) -> None:
        if not 0.0 <= self.cluster_health <= 100.0:
            raise ValueError("cluster_health must be in [0, 100]")
        if self.predicted_latency < 0.0:
            raise ValueError("predicted_latency must be >= 0")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")
