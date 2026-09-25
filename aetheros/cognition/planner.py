"""Cognitive planner — intervention plans evaluated via simulation.

Recommendation-only. Humans approve. Never executes OS changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aetheros.cognition.hypotheses import Observation
from aetheros.cognition.verifier import VerifiedExplanation
from aetheros.intent.models import IntentProfile
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.simulation.engine import SimulatableStrategy, SimulationEngine
from aetheros.simulation.models import SimulationResult


@dataclass(frozen=True, slots=True)
class InterventionPlan:
    """One immutable intervention plan (advice only).

    Attributes:
        plan_id: latency | efficiency | balanced.
        title: Display name.
        summary: Operator-facing description.
        strategy: Simulation strategy deltas.
        simulation: Result of what-if evaluation, if run.
        score: Combined suitability 0–100.
    """

    plan_id: str
    title: str
    summary: str
    strategy: SimulatableStrategy
    simulation: SimulationResult | None
    score: int


@dataclass(frozen=True, slots=True)
class PlanSet:
    """Ranked intervention plans for an observation."""

    observation: Observation
    verified: VerifiedExplanation | None
    plans: tuple[InterventionPlan, ...]
    recommended: InterventionPlan | None
    status: str = "Recommendation only — human approval required. No execution."


@dataclass
class CognitivePlanner:
    """Generate and simulate Latency / Efficiency / Balanced plans."""

    simulator: SimulationEngine = field(default_factory=SimulationEngine)

    def plan(
        self,
        observation: Observation,
        snapshot: TelemetrySnapshot,
        intent: IntentProfile,
        *,
        verified: VerifiedExplanation | None = None,
    ) -> PlanSet:
        """Build three plans, simulate each, rank by score."""

        drafts = (
            self._latency_plan(observation),
            self._efficiency_plan(observation),
            self._balanced_plan(observation),
        )
        evaluated: list[InterventionPlan] = []
        for draft in drafts:
            sim = self.simulator.simulate(draft.strategy, snapshot, intent)
            score = _score_plan(draft.plan_id, sim, intent, verified)
            evaluated.append(
                InterventionPlan(
                    plan_id=draft.plan_id,
                    title=draft.title,
                    summary=draft.summary,
                    strategy=draft.strategy,
                    simulation=sim,
                    score=score,
                )
            )
        ranked = tuple(sorted(evaluated, key=lambda p: (-p.score, p.title)))
        return PlanSet(
            observation=observation,
            verified=verified,
            plans=ranked,
            recommended=ranked[0] if ranked else None,
        )

    def _latency_plan(self, observation: Observation) -> InterventionPlan:
        """Interactive / low-latency oriented plan."""

        strategy = SimulatableStrategy(
            title="Latency Plan",
            description="Favor interactive priority; reduce background contention.",
            expected_cpu_delta=-12.0 if observation.metric == "cpu" else -6.0,
            expected_memory_delta=-3.0,
            expected_efficiency_delta=4.0,
        )
        return InterventionPlan(
            plan_id="latency",
            title="Latency Plan",
            summary="Prioritize interactive responsiveness (advice only).",
            strategy=strategy,
            simulation=None,
            score=0,
        )

    def _efficiency_plan(self, observation: Observation) -> InterventionPlan:
        """Power / background reduction plan."""

        strategy = SimulatableStrategy(
            title="Efficiency Plan",
            description="Trim background work; prefer efficiency.",
            expected_cpu_delta=-10.0,
            expected_memory_delta=-4.0,
            expected_efficiency_delta=12.0,
        )
        return InterventionPlan(
            plan_id="efficiency",
            title="Efficiency Plan",
            summary="Reduce background load and favor efficiency (advice only).",
            strategy=strategy,
            simulation=None,
            score=0,
        )

    def _balanced_plan(self, observation: Observation) -> InterventionPlan:
        """Blend of latency and efficiency."""

        _ = observation
        strategy = SimulatableStrategy(
            title="Balanced Plan",
            description="Moderate relief across CPU, memory, and efficiency.",
            expected_cpu_delta=-7.0,
            expected_memory_delta=-3.0,
            expected_efficiency_delta=7.0,
        )
        return InterventionPlan(
            plan_id="balanced",
            title="Balanced Plan",
            summary="Balanced responsiveness and efficiency (advice only).",
            strategy=strategy,
            simulation=None,
            score=0,
        )


def _score_plan(
    plan_id: str,
    simulation: SimulationResult,
    intent: IntentProfile,
    verified: VerifiedExplanation | None,
) -> int:
    """Score a simulated plan using intent alignment and stability."""

    base = simulation.overall_improvement * 0.5 + simulation.stability_score * 0.35
    if plan_id == "latency":
        base += intent.latency_weight * 0.4
    elif plan_id == "efficiency":
        base += intent.efficiency_weight * 0.4
    else:
        base += (intent.latency_weight + intent.efficiency_weight) * 0.15
    if verified is not None and verified.result is not None:
        base += verified.confidence * 0.1
    return int(max(0, min(100, round(base))))


# ---------------------------------------------------------------------------
# v3 Cognition Core planner — simulation-backed recommendation plans only
# ---------------------------------------------------------------------------


def generate_cognition_plans(
    *,
    verified: tuple = (),
    simulation_agreement: float | None = None,
    context_label: str = "BALANCED",
) -> tuple:
    """Emit Performance / Efficiency / Balanced plans when simulation-backed.

    Plans are advice-only. Without a simulation signal, returns empty —
    never invents executable actions.
    """

    from aetheros.cognition.models import CognitionPlan

    has_sim_reason = any(any("Simulation" in r for r in v.reasons) for v in verified)
    if simulation_agreement is None and not has_sim_reason:
        return ()

    base = simulation_agreement if simulation_agreement is not None else 75.0
    top = verified[0] if verified else None
    conf = round(min(95.0, base * 0.7 + (top.confidence * 0.3 if top else 20.0)), 2)
    label = context_label

    return (
        CognitionPlan(
            kind="performance",
            title="Performance Plan",
            summary=(
                f"Prioritize responsiveness for {label} by reducing foreground "
                f"CPU contention (simulation-backed advice)."
            ),
            steps=(
                "Review top CPU-bound process edges on the resource graph",
                "Simulate reduced foreground load via Digital Twin",
                "Compare latency score before recommending operator action",
            ),
            simulation_backed=True,
            confidence=conf,
        ),
        CognitionPlan(
            kind="efficiency",
            title="Efficiency Plan",
            summary=(
                f"Prioritize efficiency for {label} by easing sustained resource "
                f"pressure (simulation-backed advice)."
            ),
            steps=(
                "Identify memory/disk pressure paths from evidence",
                "Simulate efficiency-oriented deltas",
                "Recommend batching or deferring non-critical workloads",
            ),
            simulation_backed=True,
            confidence=max(50.0, conf - 3.0),
        ),
        CognitionPlan(
            kind="balanced",
            title="Balanced Plan",
            summary=(
                f"Balance responsiveness and efficiency under {label} "
                f"(simulation-backed advice)."
            ),
            steps=(
                "Keep verified explanations visible to the operator",
                "Simulate a mixed latency/efficiency scenario",
                "Present trade-offs; await human approval",
            ),
            simulation_backed=True,
            confidence=max(50.0, conf - 1.5),
        ),
    )
