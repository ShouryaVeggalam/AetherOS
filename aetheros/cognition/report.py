"""Cognitive cycle report — owned by ``aetheros.cognition``.

Narrative assembly over verified cognition outputs. Lives here (not in
``reasoning``) so cognition runtime/renderer do not import reasoning.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.cognition.causal_graph import CausalGraph
from aetheros.cognition.hypotheses import HypothesisSet, Observation
from aetheros.cognition.planner import PlanSet
from aetheros.cognition.verifier import VerifiedExplanation


@dataclass(frozen=True, slots=True)
class CognitiveReport:
    """Immutable cognitive cycle report for UI / API."""

    observation: Observation
    hypotheses: HypothesisSet
    verified: VerifiedExplanation
    plans: PlanSet | None
    graph: CausalGraph
    memory_notes: tuple[str, ...]
    narrative: tuple[str, ...]
    confidence: int
    status: str = "Recommendation only — humans always approve actions."


def build_cognitive_report(
    *,
    observation: Observation,
    hypotheses: HypothesisSet,
    verified: VerifiedExplanation,
    plans: PlanSet | None,
    graph: CausalGraph,
    memory_notes: tuple[str, ...] = (),
) -> CognitiveReport:
    """Assemble a CognitiveReport with a structured narrative."""

    narrative = explain_reasoning(
        observation=observation,
        hypotheses=hypotheses,
        verified=verified,
        plans=plans,
        memory_notes=memory_notes,
    )
    confidence = verified.confidence
    if plans is not None and plans.recommended is not None:
        confidence = max(confidence, min(99, plans.recommended.score))
    return CognitiveReport(
        observation=observation,
        hypotheses=hypotheses,
        verified=verified,
        plans=plans,
        graph=graph,
        memory_notes=memory_notes,
        narrative=narrative,
        confidence=int(confidence),
    )


def explain_reasoning(
    *,
    observation: Observation,
    hypotheses: HypothesisSet,
    verified: VerifiedExplanation,
    plans: PlanSet | None,
    memory_notes: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Produce research-quality explanation lines."""

    lines: list[str] = [
        f"Observation: {observation.summary}",
    ]
    if hypotheses.hypotheses:
        lines.append("Hypotheses considered:")
        for hyp in hypotheses.hypotheses[:4]:
            lines.append(f"  • {hyp.title} ({hyp.probability:.0%})")
    if verified.result is not None:
        hyp = verified.result.hypothesis
        lines.append(f"Hypothesis: {hyp.description}")
        lines.append("Evidence:")
        for item in verified.result.reasons[:5]:
            lines.append(f"  • {item}")
        for note in memory_notes[:3]:
            lines.append(f"  • Memory: {note}")
        lines.append(
            f"Conclusion: verified explanation with confidence "
            f"{verified.confidence}%."
        )
    else:
        lines.append("Conclusion: no hypothesis met the verification threshold.")
    if plans is not None and plans.recommended is not None:
        rec = plans.recommended
        lines.append(
            f"Recommended plan: {rec.title} (score {rec.score}) — advice only."
        )
        if rec.simulation is not None:
            lines.append(
                f"Simulation: projected CPU "
                f"{rec.simulation.projected_cpu_percent:.0f}%, "
                f"stability {rec.simulation.stability_score:.0f}."
            )
    return tuple(lines)
