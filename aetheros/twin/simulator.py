"""Global Twin simulator — worldwide infrastructure what-ifs.

Also hosts Digital Twin 2.0 (P7) ``DigitalTwinSimulator`` for ResourceGraph
scenarios. Simulation only. Never affects real regions, devices, or the host OS.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from aetheros.twin.models import (
    SimulationResult,
    SimulationScenario,
    SnapshotDiff,
    TwinSnapshot,
)

ScenarioKind = Literal[
    "region_outage",
    "gpu_shortage",
    "network_congestion",
    "edge_expansion",
]


@dataclass(frozen=True, slots=True)
class TwinScenario:
    """One immutable global twin scenario."""

    scenario_id: str
    kind: ScenarioKind
    title: str
    description: str
    intensity: float

    def __post_init__(self) -> None:
        """Validate intensity 0–100."""

        if not 0.0 <= self.intensity <= 100.0:
            raise ValueError("intensity must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class TwinOutcome:
    """Immutable simulation outcome for one scenario."""

    scenario: TwinScenario
    capacity: float
    stability: float
    latency: float
    risk: float
    explanation: str
    confidence: float


SEED_SCENARIOS: tuple[TwinScenario, ...] = (
    TwinScenario(
        "twin.region_outage",
        "region_outage",
        "Cloud Region Outage",
        "Simulate loss of one cloud region capacity.",
        25.0,
    ),
    TwinScenario(
        "twin.gpu_shortage",
        "gpu_shortage",
        "GPU Shortage",
        "Simulate constrained GPU pool availability.",
        40.0,
    ),
    TwinScenario(
        "twin.network_congestion",
        "network_congestion",
        "Network Congestion",
        "Simulate backbone congestion across regions.",
        30.0,
    ),
    TwinScenario(
        "twin.edge_expansion",
        "edge_expansion",
        "Edge Device Expansion",
        "Simulate adding edge capacity / devices.",
        20.0,
    ),
)


@dataclass
class TwinSimulator:
    """Score global twin scenarios with pure math."""

    def simulate(self, scenario: TwinScenario) -> TwinOutcome:
        """Project capacity / stability / latency / risk for ``scenario``."""

        intensity = scenario.intensity
        if scenario.kind == "edge_expansion":
            capacity = min(100.0, 85.0 + intensity * 0.25)
            stability = min(100.0, 88.0 + intensity * 0.1)
            latency = max(5.0, 35.0 - intensity * 0.2)
            risk = max(5.0, 25.0 - intensity * 0.15)
        elif scenario.kind == "region_outage":
            capacity = max(20.0, 100.0 - intensity * 1.1)
            stability = max(15.0, 95.0 - intensity * 1.2)
            latency = min(100.0, 20.0 + intensity * 1.4)
            risk = min(100.0, 20.0 + intensity * 1.5)
        elif scenario.kind == "gpu_shortage":
            capacity = max(25.0, 90.0 - intensity * 1.0)
            stability = max(30.0, 88.0 - intensity * 0.7)
            latency = min(100.0, 25.0 + intensity * 0.9)
            risk = min(100.0, 30.0 + intensity * 1.1)
        else:  # network_congestion
            capacity = max(40.0, 92.0 - intensity * 0.4)
            stability = max(35.0, 90.0 - intensity * 0.8)
            latency = min(100.0, 18.0 + intensity * 1.6)
            risk = min(100.0, 22.0 + intensity * 1.2)

        explanation = (
            f"Simulated '{scenario.title}' at intensity {intensity:.0f}%: "
            f"capacity {capacity:.1f}, stability {stability:.1f}, "
            f"latency {latency:.1f}, risk {risk:.1f}. Simulation only."
        )
        confidence = 0.82 if intensity < 50 else 0.74
        return TwinOutcome(
            scenario=scenario,
            capacity=round(capacity, 1),
            stability=round(stability, 1),
            latency=round(latency, 1),
            risk=round(risk, 1),
            explanation=explanation,
            confidence=confidence,
        )


# ---------------------------------------------------------------------------
# Digital Twin 2.0 — host ResourceGraph what-if runner (P7)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class DigitalTwinReport:
    """Immutable host twin run: baseline, simulated, result, and diff."""

    baseline: TwinSnapshot
    simulated: TwinSnapshot
    result: SimulationResult
    diff: SnapshotDiff


@dataclass
class DigitalTwinSimulator:
    """Run host Digital Twin scenarios on cloned snapshots only.

    Pipeline: snapshot → clone → apply scenario → evaluate → diff.
    Never reads or writes live host state beyond the provided snapshot.
    """

    def run(
        self,
        snapshot: TwinSnapshot,
        scenario: SimulationScenario,
        *,
        now: datetime | None = None,
    ) -> DigitalTwinReport:
        """Execute one scenario against a cloned twin sandbox."""

        from aetheros.twin.diff import diff_twins
        from aetheros.twin.evaluator import evaluate
        from aetheros.twin.scenario import apply_scenario
        from aetheros.twin.snapshot import clone_snapshot

        baseline = clone_snapshot(snapshot, now=now)
        simulated = apply_scenario(baseline, scenario, now=now)
        result = evaluate(baseline, simulated, scenario)
        diff = diff_twins(baseline, simulated)
        return DigitalTwinReport(
            baseline=baseline,
            simulated=simulated,
            result=result,
            diff=diff,
        )
