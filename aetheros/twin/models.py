"""Digital Twin 2.0 models — immutable host twin contracts.

Distinct from Fabric global twin (``TwinScenario`` / ``TwinOutcome``).
Host twin results are predictions only — never applied to the live system.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from aetheros.graph.models import ResourceGraph
from aetheros.policy_engine.models import TelemetrySnapshot

ScenarioKind = Literal[
    "CPU_OVERLOAD",
    "MEMORY_PRESSURE",
    "BATTERY_LOW",
    "DISK_SATURATION",
    "NODE_OFFLINE",
    "CUSTOM",
]

RiskLevel = Literal["low", "medium", "high", "critical"]


@dataclass(frozen=True, slots=True)
class MetricChange:
    """One immutable metric delta between snapshots."""

    metric: str
    before: float | None
    after: float | None


@dataclass(frozen=True, slots=True)
class TwinSnapshot:
    """Immutable point-in-time copy of host intelligence state.

    Attributes:
        id: Stable snapshot identifier.
        timestamp: Capture time (UTC).
        resource_graph: Cloned ResourceGraph (never the live instance).
        telemetry: Flat telemetry accompanying the graph.
        intent: Active intent name, or None.
    """

    id: str
    timestamp: datetime
    resource_graph: ResourceGraph
    telemetry: TelemetrySnapshot
    intent: str | None


@dataclass(frozen=True, slots=True)
class SimulationScenario:
    """One immutable what-if scenario applied only to cloned twins.

    Attributes:
        name: Scenario kind key.
        description: Operator-facing explanation.
        modifications: Frozen key/value deltas (e.g. cpu_delta=+30).
        created_at: Scenario materialisation time.
    """

    name: ScenarioKind
    description: str
    modifications: tuple[tuple[str, str], ...]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Predicted outcome of one Digital Twin scenario run.

    Attributes:
        predicted_cpu: Forecast CPU percent 0–100.
        predicted_memory: Forecast memory percent 0–100.
        predicted_disk: Forecast disk percent 0–100.
        predicted_battery: Forecast battery percent, or None.
        stability: Stability score 0–100.
        confidence: Confidence 0–100.
        reasoning: Graph/reasoning-derived explanation text.
        risk: Discrete risk level.
        bottleneck: Primary bottleneck resource key.
        scenario: Scenario that produced this result.
    """

    predicted_cpu: float
    predicted_memory: float
    predicted_disk: float
    predicted_battery: float | None
    stability: float
    confidence: float
    reasoning: str
    risk: RiskLevel
    bottleneck: str
    scenario: SimulationScenario

    def __post_init__(self) -> None:
        """Validate score bounds."""

        for label, value in (
            ("stability", self.stability),
            ("confidence", self.confidence),
            ("predicted_cpu", self.predicted_cpu),
            ("predicted_memory", self.predicted_memory),
            ("predicted_disk", self.predicted_disk),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(f"{label} must be in [0, 100]")
        if (
            self.predicted_battery is not None
            and not 0.0 <= self.predicted_battery <= 100.0
        ):
            raise ValueError("predicted_battery must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class SnapshotDiff:
    """Immutable comparison between baseline and simulated twin snapshots."""

    added_nodes: frozenset[str]
    removed_nodes: frozenset[str]
    changed_metrics: tuple[MetricChange, ...]
    changed_edges: frozenset[str]
