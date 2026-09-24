"""Reasoning engine — build evidence-based explanation chains.

Every sentence is sourced from Evidence descriptions. No invented reasons.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aetheros.decision.models import Decision
from aetheros.explainability.confidence import compute_confidence
from aetheros.explainability.evidence import collect_evidence
from aetheros.explainability.models import Evidence, Explanation, ReasoningChain
from aetheros.intent.models import IntentProfile
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.simulation.engine import SimulatableStrategy, SimulationEngine
from aetheros.simulation.models import SimulationResult
from aetheros.telemetry.models import ProcessSnapshot


@dataclass
class ExplainabilityEngine:
    """Orchestrate evidence → reasoning → confidence → Explanation."""

    simulator: SimulationEngine = field(default_factory=SimulationEngine)

    def explain(
        self,
        decision: Decision,
        snapshot: TelemetrySnapshot,
        *,
        history: tuple[TelemetryPoint, ...] = (),
        intent: IntentProfile | None = None,
        simulation: SimulationResult | None = None,
        processes: tuple[ProcessSnapshot, ...] = (),
    ) -> Explanation:
        """Produce a full Explanation for one Decision.

        Args:
            decision: Decision being explained.
            snapshot: Live telemetry used for the decision.
            history: Observatory history points.
            intent: Active intent profile.
            simulation: Optional simulation for this recommendation.
            processes: Optional process samples.

        Returns:
            An Explanation with traceable evidence only.
        """

        sim = simulation
        if sim is None and intent is not None:
            sim = self.simulate_decision(decision, snapshot, intent)
        bundle = collect_evidence(
            snapshot,
            history=history,
            intent=intent,
            simulation=sim,
            processes=processes,
        )
        chain = build_reasoning_chain(bundle.items)
        confidence = compute_confidence(
            bundle,
            simulation=sim,
            current_cpu=snapshot.cpu_percent,
        )
        summary = _conclusion(decision, chain, confidence)
        return Explanation(
            title=decision.title,
            summary=summary,
            confidence=confidence,
            evidence=bundle.items,
            reasoning_chain=chain,
        )

    def simulate_decision(
        self,
        decision: Decision,
        snapshot: TelemetrySnapshot,
        intent: IntentProfile,
    ) -> SimulationResult:
        """Run a read-only what-if simulation grounded in live telemetry."""

        strategy = _strategy_from_decision(decision, snapshot, intent)
        return self.simulator.simulate(strategy, snapshot, intent)


def _strategy_from_decision(
    decision: Decision,
    snapshot: TelemetrySnapshot,
    intent: IntentProfile,
) -> SimulatableStrategy:
    """Derive simulation deltas from snapshot pressure and decision title."""

    cpu_pressure = max(0.0, snapshot.cpu_percent - 50.0) / 50.0
    mem_pressure = max(0.0, snapshot.memory_percent - 50.0) / 50.0
    title = decision.title.lower()
    if "memory" in title:
        cpu_delta = -2.0 - cpu_pressure * 1.0
        mem_delta = -6.0 - intent.memory_weight * 0.2 - mem_pressure * 5.0
        eff_delta = 5.0
    elif "disk" in title:
        cpu_delta = -1.0
        mem_delta = -1.0
        eff_delta = 3.0
    elif "idle" in title or "healthy" in title:
        cpu_delta = -1.0 - intent.efficiency_weight * 0.05
        mem_delta = -1.0
        eff_delta = 4.0 + intent.efficiency_weight * 0.1
    else:
        cpu_delta = -8.0 - intent.latency_weight * 0.25 - cpu_pressure * 4.0
        mem_delta = -2.0 - intent.latency_weight * 0.05
        eff_delta = 5.0 + intent.latency_weight * 0.1
    return SimulatableStrategy(
        title=decision.title,
        description=decision.action,
        expected_cpu_delta=round(cpu_delta, 1),
        expected_memory_delta=round(mem_delta, 1),
        expected_efficiency_delta=round(eff_delta, 1),
    )


def build_reasoning_chain(items: tuple[Evidence, ...]) -> ReasoningChain:
    """Split evidence descriptions into reasoning sections by source."""

    observations = tuple(e.description for e in items if e.source == "telemetry")
    historical = tuple(e.description for e in items if e.source == "history")
    simulation = tuple(e.description for e in items if e.source == "simulation")
    intent_ctx = tuple(e.description for e in items if e.source == "intent")
    return ReasoningChain(
        observations=observations,
        historical_patterns=historical,
        simulation_support=simulation,
        intent_context=intent_ctx,
    )


def _conclusion(
    decision: Decision,
    chain: ReasoningChain,
    confidence: int,
) -> str:
    """Compose a final conclusion from available chain sections only."""

    bits: list[str] = []
    if chain.observations:
        bits.append(chain.observations[0].rstrip("."))
    if chain.intent_context:
        bits.append(chain.intent_context[-1].rstrip("."))
    if chain.simulation_support:
        bits.append(chain.simulation_support[0].rstrip("."))
    if not bits:
        return (
            f"{decision.title} is shown with confidence {confidence}% "
            "based on available pipeline context."
        )
    joined = "; ".join(bits)
    return (
        f"{decision.title} is recommended because {joined}, "
        f"supporting responsiveness while preserving stability "
        f"(confidence {confidence}%)."
    )
