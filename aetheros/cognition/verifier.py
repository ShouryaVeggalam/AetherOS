"""Hypothesis verifier — reject unsupported explanations using history.

Only telemetry-backed hypotheses become verified recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.cognition.hypotheses import Hypothesis, HypothesisSet, Observation
from aetheros.cognition.memory import CognitiveFact, CognitiveMemory
from aetheros.observatory.models import TelemetryPoint


@dataclass(frozen=True, slots=True)
class VerificationResult:
    """Outcome of verifying one hypothesis.

    Attributes:
        hypothesis: Candidate under review.
        verified: True when supported by history/memory evidence.
        support_score: 0.0–1.0 measured support.
        reasons: Why accepted or rejected.
    """

    hypothesis: Hypothesis
    verified: bool
    support_score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class VerifiedExplanation:
    """Best verified hypothesis for an observation (if any)."""

    observation: Observation
    result: VerificationResult | None
    rejected: tuple[VerificationResult, ...]
    confidence: int


def verify_hypotheses(
    hypothesis_set: HypothesisSet,
    *,
    history: tuple[TelemetryPoint, ...] = (),
    memory: CognitiveMemory | None = None,
    min_support: float = 0.35,
) -> VerifiedExplanation:
    """Verify each hypothesis; pick the best supported one.

    Args:
        hypothesis_set: Generated candidates.
        history: Observatory telemetry points.
        memory: Cognitive memory facts.
        min_support: Minimum support_score to accept.

    Returns:
        VerifiedExplanation with recommendation-only semantics.
    """

    facts = memory.list_facts() if memory is not None else ()
    results: list[VerificationResult] = []
    for hyp in hypothesis_set.hypotheses:
        results.append(
            _verify_one(
                hyp,
                hypothesis_set.observation,
                history=history,
                facts=facts,
                min_support=min_support,
            )
        )
    verified = [r for r in results if r.verified]
    verified.sort(key=lambda r: (-r.support_score, -r.hypothesis.probability))
    rejected = tuple(r for r in results if not r.verified)
    best = verified[0] if verified else None
    confidence = int(round(best.support_score * 100)) if best is not None else 0
    return VerifiedExplanation(
        observation=hypothesis_set.observation,
        result=best,
        rejected=rejected,
        confidence=confidence,
    )


def _verify_one(
    hyp: Hypothesis,
    observation: Observation,
    *,
    history: tuple[TelemetryPoint, ...],
    facts: tuple[CognitiveFact, ...],
    min_support: float,
) -> VerificationResult:
    """Score support for one hypothesis."""

    reasons: list[str] = []
    score = 0.0

    # Prior probability contributes modestly.
    score += hyp.probability * 0.35
    reasons.append(f"Prior probability {hyp.probability:.0%}.")

    if hyp.related_process:
        score += 0.25
        reasons.append(f"Process evidence present: {hyp.related_process}.")
    elif hyp.hypothesis_id == "simulation_workload":
        # Simulation is rarely the cause of host CPU — require more support.
        score -= 0.1
        reasons.append("No live process match for simulation workload.")

    metric = observation.metric
    if history:
        recent = history[-min(60, len(history)) :]
        values = [float(getattr(p, metric, 0.0)) for p in recent]
        if values:
            avg = sum(values) / len(values)
            if avg >= 85.0:
                score += 0.2
                reasons.append(
                    f"History average {metric} {avg:.0f}% supports sustained pressure."
                )
            elif avg < 50.0:
                score -= 0.15
                reasons.append(
                    f"History average {metric} {avg:.0f}% weakens sustained-load claims."
                )

    for fact in facts:
        if _fact_supports(hyp, fact):
            score += 0.15 * fact.confidence
            reasons.append(f"Memory fact: {fact.notes}")
            break

    score = max(0.0, min(1.0, score))
    verified = score >= min_support and len(reasons) >= 2
    if not verified:
        reasons.append("Rejected: insufficient telemetry/memory support.")
    else:
        reasons.append("Accepted: evidence meets verification threshold.")
    return VerificationResult(
        hypothesis=hyp,
        verified=verified,
        support_score=round(score, 4),
        reasons=tuple(reasons),
    )


def _fact_supports(hyp: Hypothesis, fact: CognitiveFact) -> bool:
    """Return True when a memory fact aligns with the hypothesis."""

    blob = f"{hyp.title} {hyp.description} {hyp.related_process or ''}".lower()
    return (
        fact.subject.lower() in blob
        or any(token in blob for token in fact.subject.lower().split())
        or fact.object.lower() in blob
    )
