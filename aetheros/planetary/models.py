"""Planetary Scheduler models — immutable global placement contracts.

v6.0 P4. Recommendations only. Never deploys workloads, never calls
Kubernetes / cloud provisioners / Terraform. Simulation-backed advice.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

ConstraintKind = Literal[
    "REGION_LOCK",
    "LATENCY_MAX",
    "REQUIRE_GPU",
    "AVOID_DEGRADED",
    "ENERGY_PRIORITY",
    "COMPLIANCE_REGION",
]

CONSTRAINT_KINDS: frozenset[str] = frozenset(
    {
        "REGION_LOCK",
        "LATENCY_MAX",
        "REQUIRE_GPU",
        "AVOID_DEGRADED",
        "ENERGY_PRIORITY",
        "COMPLIANCE_REGION",
    }
)


@dataclass(frozen=True, slots=True)
class GlobalWorkload:
    """One immutable global workload request (advice input only)."""

    id: str
    name: str
    cpu: float
    memory: float
    gpu: float = 0.0
    region_preference: str = ""
    latency_target: float = 50.0

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        for name in ("cpu", "memory", "gpu"):
            if float(getattr(self, name)) < 0.0:
                raise ValueError(f"{name} must be non-negative")
        if self.latency_target <= 0.0:
            raise ValueError("latency_target must be positive")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "id": self.id,
            "name": self.name,
            "cpu": self.cpu,
            "memory": self.memory,
            "gpu": self.gpu,
            "region_preference": self.region_preference,
            "latency_target": self.latency_target,
        }


@dataclass(frozen=True, slots=True)
class PlacementSite:
    """One immutable planetary placement site (census row)."""

    region: str
    datacenter: str
    cluster: str
    node: str
    cpu_available: float
    memory_available: float
    gpu_available: float = 0.0
    latency_ms: float = 20.0
    cluster_health: float = 95.0
    energy_efficiency: float = 70.0
    regional_resilience: float = 90.0
    degraded: bool = False
    compliance_tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("region", "datacenter", "cluster", "node"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"{name} must be non-empty")
        for name in (
            "cpu_available",
            "memory_available",
            "gpu_available",
            "cluster_health",
            "energy_efficiency",
            "regional_resilience",
        ):
            value = float(getattr(self, name))
            if value < 0.0:
                raise ValueError(f"{name} must be non-negative")
        if self.latency_ms < 0.0:
            raise ValueError("latency_ms must be non-negative")
        object.__setattr__(self, "compliance_tags", tuple(self.compliance_tags))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def site_id(self) -> str:
        """Stable composite site identifier."""

        return f"{self.region}/{self.datacenter}/{self.cluster}/{self.node}"


@dataclass(frozen=True, slots=True)
class Candidate:
    """One scored placement candidate (recommendation only)."""

    region: str
    datacenter: str
    cluster: str
    node: str
    score: float
    latency_ms: float = 0.0
    availability: float = 0.0
    reasoning: str = ""
    trade_off: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 100.0:
            raise ValueError("score must be in [0, 100]")
        if self.latency_ms < 0.0:
            raise ValueError("latency_ms must be non-negative")
        if not 0.0 <= self.availability <= 100.0:
            raise ValueError("availability must be in [0, 100]")

    @property
    def site_id(self) -> str:
        return f"{self.region}/{self.datacenter}/{self.cluster}/{self.node}"

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "region": self.region,
            "datacenter": self.datacenter,
            "cluster": self.cluster,
            "node": self.node,
            "score": self.score,
            "latency_ms": self.latency_ms,
            "availability": self.availability,
            "reasoning": self.reasoning,
            "trade_off": self.trade_off,
        }


@dataclass(frozen=True, slots=True)
class PlanetaryConstraint:
    """One hard placement constraint applied before scoring."""

    kind: ConstraintKind
    value: float | str = 0.0

    def __post_init__(self) -> None:
        if self.kind not in CONSTRAINT_KINDS:
            raise ValueError(f"invalid constraint kind: {self.kind}")


@dataclass(frozen=True, slots=True)
class PlacementSimulation:
    """Twin-backed simulation metrics for one candidate site (read-only)."""

    site_id: str
    latency_ms: float
    availability: float
    cpu: float
    memory: float
    failure_resilience: float
    twin_confidence: float = 80.0

    def __post_init__(self) -> None:
        if not self.site_id.strip():
            raise ValueError("site_id must be non-empty")
        if self.latency_ms < 0.0:
            raise ValueError("latency_ms must be non-negative")
        for name in ("availability", "cpu", "memory", "failure_resilience", "twin_confidence"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be in [0, 100]")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "site_id": self.site_id,
            "latency_ms": self.latency_ms,
            "availability": self.availability,
            "cpu": self.cpu,
            "memory": self.memory,
            "failure_resilience": self.failure_resilience,
            "twin_confidence": self.twin_confidence,
        }


@dataclass(frozen=True, slots=True)
class ScheduleDecision:
    """Immutable planetary schedule recommendation (never executed)."""

    workload: GlobalWorkload
    best_candidate: Candidate | None
    alternatives: tuple[Candidate, ...]
    confidence: float
    reasoning: str
    simulations: tuple[PlacementSimulation, ...] = ()
    rejected: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")
        object.__setattr__(self, "alternatives", tuple(self.alternatives))
        object.__setattr__(self, "simulations", tuple(self.simulations))
        object.__setattr__(self, "rejected", tuple(self.rejected))

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "workload": self.workload.to_dict(),
            "best_candidate": (
                self.best_candidate.to_dict() if self.best_candidate else None
            ),
            "alternatives": [c.to_dict() for c in self.alternatives],
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "simulations": [s.to_dict() for s in self.simulations],
            "rejected": [{"site_id": s, "reason": r} for s, r in self.rejected],
        }
