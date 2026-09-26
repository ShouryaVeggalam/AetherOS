"""Infrastructure Digital Twin models — immutable simulation contracts.

v6.0 P2. Simulation only. Never represents cloud mutations, Terraform,
kubectl, or live API writes. All scenarios operate on cloned snapshots.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

ScenarioKind = Literal[
    "REGION_OUTAGE",
    "NODE_FAILURE",
    "NETWORK_LATENCY",
    "GPU_EXPANSION",
    "WORKLOAD_SURGE",
    "DISK_FAILURE",
    "CUSTOM",
]

SCENARIO_KINDS: frozenset[str] = frozenset(
    {
        "REGION_OUTAGE",
        "NODE_FAILURE",
        "NETWORK_LATENCY",
        "GPU_EXPANSION",
        "WORKLOAD_SURGE",
        "DISK_FAILURE",
        "CUSTOM",
    }
)

RiskLevel = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True, slots=True)
class TopologyNode:
    """One node in the twin topology graph (read-only census)."""

    id: str
    kind: str
    region: str
    provider: str
    capacity: float = 100.0
    load: float = 40.0
    latency_ms: float = 4.0
    available: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.kind.strip():
            raise ValueError("kind must be non-empty")
        if not self.region.strip():
            raise ValueError("region must be non-empty")
        if not 0.0 <= self.capacity <= 1000.0:
            raise ValueError("capacity out of range")
        if not 0.0 <= self.load <= 100.0:
            raise ValueError("load must be in [0, 100]")
        if self.latency_ms < 0.0:
            raise ValueError("latency_ms must be non-negative")
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON / cloning."""

        return {
            "id": self.id,
            "kind": self.kind,
            "region": self.region,
            "provider": self.provider,
            "capacity": self.capacity,
            "load": self.load,
            "latency_ms": self.latency_ms,
            "available": self.available,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TopologyNode:
        """Parse a TopologyNode from a mapping."""

        meta = data.get("metadata") or {}
        if not isinstance(meta, Mapping):
            raise ValueError("metadata must be a mapping")
        return cls(
            id=str(data.get("id") or "").strip(),
            kind=str(data.get("kind") or "node").strip(),
            region=str(data.get("region") or "").strip(),
            provider=str(data.get("provider") or "unknown").strip(),
            capacity=float(
                data.get("capacity") if data.get("capacity") is not None else 100.0
            ),
            load=float(data.get("load") if data.get("load") is not None else 40.0),
            latency_ms=float(
                data.get("latency_ms") if data.get("latency_ms") is not None else 4.0
            ),
            available=bool(data.get("available", True)),
            metadata=dict(meta),
        )


@dataclass(frozen=True, slots=True)
class InfrastructureSnapshot:
    """Immutable twin world-state (cloned before any scenario).

    Distinct from ``aetheros.cloud.models.InfrastructureSnapshot`` (federation
    census). This twin snapshot carries topology + utilization for simulation.
    """

    id: str
    timestamp: datetime
    topology: tuple[TopologyNode, ...]
    resources: tuple[str, ...]
    regions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        object.__setattr__(self, "topology", tuple(self.topology))
        object.__setattr__(self, "resources", tuple(self.resources))
        object.__setattr__(self, "regions", tuple(self.regions))

    @property
    def node_count(self) -> int:
        """Number of topology nodes."""

        return len(self.topology)

    @property
    def available_nodes(self) -> int:
        """Count of currently available nodes."""

        return sum(1 for n in self.topology if n.available)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "topology": [n.to_dict() for n in self.topology],
            "resources": list(self.resources),
            "regions": list(self.regions),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> InfrastructureSnapshot:
        """Parse an InfrastructureSnapshot from a mapping."""

        topo = data.get("topology") or ()
        resources = data.get("resources") or ()
        regions = data.get("regions") or ()
        if not isinstance(topo, (list, tuple)):
            raise ValueError("topology must be a list")
        if not isinstance(resources, (list, tuple)):
            raise ValueError("resources must be a list")
        if not isinstance(regions, (list, tuple)):
            raise ValueError("regions must be a list")
        return cls(
            id=str(data.get("id") or "").strip(),
            timestamp=datetime.fromisoformat(str(data.get("timestamp") or "")),
            topology=tuple(TopologyNode.from_dict(n) for n in topo),
            resources=tuple(str(r) for r in resources),
            regions=tuple(str(r) for r in regions),
        )


@dataclass(frozen=True, slots=True)
class TwinScenario:
    """One immutable what-if scenario applied only to cloned twins."""

    id: str
    name: str
    description: str
    variables: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        kind = self.name.strip().upper().replace(" ", "_")
        if kind not in SCENARIO_KINDS and self.name not in SCENARIO_KINDS:
            # Allow human titles if variables carry kind=
            if str(self.variables.get("kind", "")).upper() not in SCENARIO_KINDS:
                raise ValueError(f"unsupported scenario: {self.name!r}")
        object.__setattr__(self, "variables", dict(self.variables))

    @property
    def kind(self) -> str:
        """Resolved scenario kind token."""

        raw = str(self.variables.get("kind") or self.name).strip().upper()
        return raw.replace(" ", "_")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "variables": dict(self.variables),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> TwinScenario:
        """Parse a TwinScenario from a mapping."""

        variables = data.get("variables") or {}
        if not isinstance(variables, Mapping):
            raise ValueError("variables must be a mapping")
        return cls(
            id=str(data.get("id") or "").strip(),
            name=str(data.get("name") or "").strip(),
            description=str(data.get("description") or "").strip(),
            variables=dict(variables),
        )


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Deterministic predicted outcome of one infrastructure twin run."""

    cpu: float
    memory: float
    latency: float
    availability: float
    stability: float
    confidence: float
    risk: RiskLevel = "low"
    explanation: str = ""
    scenario_id: str = ""

    def __post_init__(self) -> None:
        for name in ("cpu", "memory", "availability", "stability", "confidence"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 100.0:
                raise ValueError(f"{name} must be in [0, 100]")
        if self.latency < 0.0:
            raise ValueError("latency must be non-negative")
        if self.risk not in ("low", "medium", "high", "critical"):
            raise ValueError(f"invalid risk: {self.risk}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "cpu": self.cpu,
            "memory": self.memory,
            "latency": self.latency,
            "availability": self.availability,
            "stability": self.stability,
            "confidence": self.confidence,
            "risk": self.risk,
            "explanation": self.explanation,
            "scenario_id": self.scenario_id,
        }


@dataclass(frozen=True, slots=True)
class InfrastructureDiff:
    """Immutable before/after twin comparison."""

    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]
    degraded: tuple[str, ...]
    nodes_before: int = 0
    nodes_after: int = 0
    latency_before: float = 0.0
    latency_after: float = 0.0
    availability_before: float = 0.0
    availability_after: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "added", tuple(self.added))
        object.__setattr__(self, "removed", tuple(self.removed))
        object.__setattr__(self, "changed", tuple(self.changed))
        object.__setattr__(self, "degraded", tuple(self.degraded))

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "added": list(self.added),
            "removed": list(self.removed),
            "changed": list(self.changed),
            "degraded": list(self.degraded),
            "nodes_before": self.nodes_before,
            "nodes_after": self.nodes_after,
            "latency_before": self.latency_before,
            "latency_after": self.latency_after,
            "availability_before": self.availability_before,
            "availability_after": self.availability_after,
        }
