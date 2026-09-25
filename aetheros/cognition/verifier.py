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


# ---------------------------------------------------------------------------
# v3 Cognition Core verifier — graph + history + simulation gates
# ---------------------------------------------------------------------------


def verify_core_hypotheses(
    hypotheses: tuple,
    evidence: tuple,
    *,
    simulation_agreement: float | None = None,
    min_confidence: float = 60.0,
    require_simulation: bool = False,
) -> tuple:
    """Accept v3 hypotheses only with multi-channel evidence support.

    Gates:
    * at least one ``resource_graph`` evidence id referenced, OR graph metric
      present in the evidence pool when hypothesis cites graph paths
    * historical support when hypothesis cites telemetry_history evidence
    * simulation agreement when provided (or required)

    Unsupported hypotheses are omitted (rejected), never forced through.
    """

    from aetheros.cognition.models import VerifiedCoreExplanation

    evidence_by_id = {e.id: e for e in evidence}
    graph_ids = {e.id for e in evidence if e.source == "resource_graph"}
    hist_ids = {e.id for e in evidence if e.source == "telemetry_history"}
    twin_ids = {e.id for e in evidence if e.source == "digital_twin"}

    accepted: list[VerifiedCoreExplanation] = []
    for hyp in hypotheses:
        refs = [
            evidence_by_id[i] for i in hyp.supporting_evidence if i in evidence_by_id
        ]
        if not refs:
            continue
        graph_support = any(e.id in graph_ids for e in refs) or any(
            e.source == "resource_graph" for e in refs
        )
        historical_support = any(e.id in hist_ids for e in refs) or any(
            e.source == "telemetry_history" for e in refs
        )
        twin_support = any(e.id in twin_ids for e in refs) or any(
            e.source == "digital_twin" for e in refs
        )

        # Require at least graph OR history evidence on the hypothesis itself.
        if not graph_support and not historical_support:
            continue

        if require_simulation and simulation_agreement is None and not twin_support:
            continue
        if simulation_agreement is not None and simulation_agreement < 70.0:
            continue

        reasons: list[str] = []
        if graph_support:
            reasons.append("Supported by resource-graph evidence.")
        if historical_support:
            reasons.append("Supported by telemetry history evidence.")
        if twin_support or simulation_agreement is not None:
            reasons.append("Simulation channel agrees or twin evidence present.")
        if not reasons:
            continue

        conf = hyp.confidence
        if graph_support and historical_support:
            conf = min(99.0, conf + 5.0)
        if simulation_agreement is not None:
            conf = min(99.0, (conf + simulation_agreement) / 2.0 + 10.0)
        if conf < min_confidence:
            continue

        accepted.append(
            VerifiedCoreExplanation(
                hypothesis=hyp,
                graph_support=graph_support,
                historical_support=historical_support,
                simulation_agreement=simulation_agreement,
                reasons=tuple(reasons),
                confidence=round(conf, 2),
            )
        )

    accepted.sort(key=lambda v: (-v.confidence, v.hypothesis.id))
    return tuple(accepted)
