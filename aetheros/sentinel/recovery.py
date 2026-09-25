"""Recovery Planner — recommend recovery strategies via Digital Twin.

Never executes recovery. Humans approve any action.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.intent.profiles import CODING, PROFILES
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.sentinel.anomaly import Anomaly
from aetheros.sentinel.cascade import CascadePrediction
from aetheros.sentinel.root_cause import RootCause
from aetheros.simulation.engine import SimulatableStrategy, SimulationEngine


@dataclass(frozen=True, slots=True)
class RecoveryStrategy:
    """One immutable recovery recommendation.

    Attributes:
        strategy_id: Stable id.
        title: Human label.
        summary: Recommendation text.
        performance: Twin performance score.
        stability: Twin stability score.
        efficiency: Twin efficiency score.
        score: Composite recommendation score.
        confidence: Belief in [0, 1].
    """

    strategy_id: str
    title: str
    summary: str
    performance: float
    stability: float
    efficiency: float
    score: float
    confidence: float


@dataclass(frozen=True, slots=True)
class RecoveryPlan:
    """Ranked recovery strategies for an incident."""

    strategies: tuple[RecoveryStrategy, ...]
    recommended: RecoveryStrategy | None
    rationale: str


@dataclass
class RecoveryPlanner:
    """Generate and score recovery strategies through simulation."""

    simulator: SimulationEngine | None = None

    def __post_init__(self) -> None:
        """Ensure simulator exists."""

        if self.simulator is None:
            self.simulator = SimulationEngine()

    def plan(
        self,
        anomaly: Anomaly,
        snapshot: TelemetrySnapshot,
        *,
        root_causes: tuple[RootCause, ...] = (),
        cascade: CascadePrediction | None = None,
    ) -> RecoveryPlan:
        """Evaluate recovery options; return recommendations only."""

        assert self.simulator is not None
        templates = _templates(anomaly, root_causes)
        scored: list[RecoveryStrategy] = []
        for strategy_id, title, summary, cpu, mem, eff in templates:
            result = self.simulator.simulate(
                SimulatableStrategy(title, summary, cpu, mem, eff),
                snapshot,
                PROFILES[CODING],
            )
            composite = (
                result.performance_score * 0.35
                + result.stability_score * 0.35
                + result.efficiency_score * 0.30
            )
            # Prefer delaying background work when indexing is top cause.
            if (
                root_causes
                and "index" in root_causes[0].cause_id
                and strategy_id == "recover.delay_index"
            ):
                composite += 8.0
            if cascade and cascade.active and strategy_id == "recover.redistribute":
                composite += 5.0
            confidence = min(0.98, 0.5 + composite / 200.0)
            scored.append(
                RecoveryStrategy(
                    strategy_id=strategy_id,
                    title=title,
                    summary=summary,
                    performance=round(result.performance_score, 1),
                    stability=round(result.stability_score, 1),
                    efficiency=round(result.efficiency_score, 1),
                    score=round(composite, 1),
                    confidence=round(confidence, 3),
                )
            )
        scored.sort(key=lambda s: s.score, reverse=True)
        recommended = scored[0] if scored else None
        rationale = (
            f"Recommended '{recommended.title}' after Digital Twin scoring."
            if recommended
            else "No recovery strategies generated."
        )
        if root_causes and recommended:
            rationale = (
                f"{rationale} Top root cause: {root_causes[0].title}. "
                "Recommendation only — humans approve actions."
            )
        return RecoveryPlan(
            strategies=tuple(scored),
            recommended=recommended,
            rationale=rationale,
        )


def _templates(
    anomaly: Anomaly,
    root_causes: tuple[RootCause, ...],
) -> tuple[tuple[str, str, str, float, float, float], ...]:
    """Strategy templates: id, title, summary, cpu/mem/eff deltas."""

    delay_note = "Delay background indexing to relieve interactive CPU."
    if root_causes and "index" in root_causes[0].cause_id:
        delay_note = (
            f"Delay background indexing — aligns with root cause "
            f"'{root_causes[0].title}'."
        )
    base = (
        (
            "recover.delay_index",
            "Delay background indexing",
            delay_note,
            -12.0,
            -2.0,
            10.0,
        ),
        (
            "recover.redistribute",
            "Redistribute workload",
            "Shed non-critical load toward cooler peers (recommendation only).",
            -10.0,
            -4.0,
            2.0,
        ),
        (
            "recover.redundancy",
            "Increase redundancy",
            "Advise adding standby capacity for critical services.",
            -4.0,
            -1.0,
            -3.0,
        ),
        (
            "recover.efficiency",
            "Enter efficiency mode",
            "Bias toward power/efficiency to stabilize constrained hosts.",
            -15.0,
            -5.0,
            14.0,
        ),
    )
    if anomaly.kind == "battery":
        return (
            base[3],
            base[0],
            base[1],
            base[2],
        )
    return base
