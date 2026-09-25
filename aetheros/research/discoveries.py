"""Discovery engine — emit discoveries only when all evidence gates pass.

Gates (all required unless noted):
* ``evidence_count >= min_evidence``
* at least one verified reasoning statement
* simulation agreement when twin evidence is provided (optional input;
  when provided must be >= ``min_simulation_agreement``)
* confidence score within bounds after composition

No LLM. No speculative discoveries.
"""

from __future__ import annotations

from collections.abc import Sequence

from aetheros.research.models import (
    Discovery,
    ResearchObservation,
    TrendAnalysis,
)

_DEFAULT_MIN_EVIDENCE = 5
_DEFAULT_MIN_SIM_AGREEMENT = 80.0
_DEFAULT_MIN_CONFIDENCE = 70.0


def verify_discoveries(
    *,
    observations: Sequence[ResearchObservation] = (),
    trends: Sequence[TrendAnalysis] = (),
    verified_reasoning: Sequence[str] = (),
    simulation_agreement: float | None = None,
    session_count: int | None = None,
    min_evidence: int = _DEFAULT_MIN_EVIDENCE,
    min_simulation_agreement: float = _DEFAULT_MIN_SIM_AGREEMENT,
    min_confidence: float = _DEFAULT_MIN_CONFIDENCE,
) -> tuple[Discovery, ...]:
    """Build discoveries from gated evidence. Returns empty if gates fail."""

    reasoning = tuple(s.strip() for s in verified_reasoning if s.strip())
    if not reasoning:
        return ()

    evidence_count = session_count if session_count is not None else len(observations)
    if evidence_count < min_evidence:
        return ()

    if simulation_agreement is not None and simulation_agreement < min_simulation_agreement:
        return ()

    discoveries: list[Discovery] = []

    # Intent / history style discovery from CPU delta observations.
    cpu_obs = [o for o in observations if o.metric == "cpu"]
    falling = [
        t
        for t in trends
        if t.metric == "cpu" and t.direction == "falling" and t.confidence >= 50.0
    ]
    if cpu_obs and falling:
        primary = max(cpu_obs, key=lambda o: o.value)
        conf = _compose_confidence(
            evidence_count=evidence_count,
            trend_confidence=falling[0].confidence,
            simulation_agreement=simulation_agreement,
        )
        if conf >= min_confidence:
            discoveries.append(
                Discovery(
                    title=(
                        f"Observed CPU relief of {primary.value:.0f}% under "
                        f"verified {falling[0].window.replace('_', ' ')} trend."
                    ),
                    summary=primary.title,
                    evidence_count=evidence_count,
                    confidence=conf,
                    supporting_reasoning=reasoning,
                    simulation_agreement=simulation_agreement,
                )
            )

    # Generic observation-backed discovery when trends alone are weak.
    if not discoveries and observations and reasoning:
        primary = observations[0]
        conf = _compose_confidence(
            evidence_count=evidence_count,
            trend_confidence=60.0,
            simulation_agreement=simulation_agreement,
        )
        if conf >= min_confidence:
            discoveries.append(
                Discovery(
                    title=primary.title.rstrip("."),
                    summary=(
                        f"{primary.title} Supported by {evidence_count} evidence "
                        f"unit(s) and verified reasoning."
                    ),
                    evidence_count=evidence_count,
                    confidence=conf,
                    supporting_reasoning=reasoning,
                    simulation_agreement=simulation_agreement,
                )
            )

    return tuple(discoveries)


def _compose_confidence(
    *,
    evidence_count: int,
    trend_confidence: float,
    simulation_agreement: float | None,
) -> float:
    evidence_score = min(40.0, evidence_count * 1.5)
    trend_score = 0.35 * trend_confidence
    sim_score = 0.25 * (simulation_agreement if simulation_agreement is not None else 70.0)
    return round(min(99.0, evidence_score + trend_score + sim_score), 2)
