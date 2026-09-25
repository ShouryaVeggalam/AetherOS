"""Critique Engine — structured self-evaluation criteria."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from labs.aether.models.types import CognitionPlan, Critique, CritiqueScore, Reflection


def critique_reasoning(
    *,
    plan: CognitionPlan,
    reasoning_summary: str,
    evidence: Sequence[str] = (),
    reflection: Reflection | None = None,
    now: datetime | None = None,
    critique_id: str | None = None,
) -> Critique:
    """Score correctness, completeness, consistency, evidence, calibration."""

    text = reasoning_summary.strip()
    if not text:
        raise ValueError("reasoning_summary must be non-empty")
    stamp = now or datetime.now(UTC)
    lower = text.lower()

    correctness = _correctness(lower, plan)
    completeness = _completeness(lower, plan, reflection)
    consistency = _consistency(lower, plan)
    evidence_quality = _evidence_quality(evidence, reflection)
    calibration = _calibration(plan, evidence, reflection)

    scores = (
        CritiqueScore(
            criterion="correctness",
            score=correctness,
            notes="causal connectives and contradiction cues",
        ),
        CritiqueScore(
            criterion="completeness",
            score=completeness,
            notes="coverage of plan stages and weaknesses addressed",
        ),
        CritiqueScore(
            criterion="consistency",
            score=consistency,
            notes="alignment with complexity and attention budget",
        ),
        CritiqueScore(
            criterion="evidence_quality",
            score=evidence_quality,
            notes="evidence count and reflection gaps",
        ),
        CritiqueScore(
            criterion="confidence_calibration",
            score=calibration,
            notes="plan confidence vs evidence/uncertainty",
        ),
    )
    overall = round(sum(s.score for s in scores) / len(scores), 4)
    verdict: str
    if overall >= 0.72:
        verdict = "pass"
    elif overall >= 0.45:
        verdict = "revise"
    else:
        verdict = "reject"

    return Critique(
        id=critique_id or f"crit_{uuid4().hex[:12]}",
        plan_id=plan.id,
        scores=scores,
        overall=overall,
        verdict=verdict,  # type: ignore[arg-type]
        created_at=stamp,
    )


def _correctness(text: str, plan: CognitionPlan) -> float:
    score = 0.45
    if any(c in text for c in ("because", "therefore", "hence", "so ")):
        score += 0.2
    if any(c in text for c in ("contradict", "inconsistent", "impossible")):
        score -= 0.25
    if plan.complexity in ("complex", "strategic") and len(text.split()) < 20:
        score -= 0.15
    if "error" in text or "wrong" in text:
        score -= 0.1
    return round(max(0.0, min(1.0, score)), 4)


def _completeness(
    text: str,
    plan: CognitionPlan,
    reflection: Reflection | None,
) -> float:
    score = 0.4
    stage_hits = sum(1 for s in plan.stages if s.name.lower() in text)
    score += min(0.3, stage_hits * 0.08)
    if reflection is not None:
        if reflection.improvements:
            score += 0.1
        if reflection.weaknesses:
            score += 0.05
    if len(text.split()) >= 40:
        score += 0.1
    return round(max(0.0, min(1.0, score)), 4)


def _consistency(text: str, plan: CognitionPlan) -> float:
    score = 0.55
    if plan.complexity == "strategic" and "strategic" in text:
        score += 0.1
    if abs(plan.confidence - 0.5) < 0.05 and "certain" in text:
        score -= 0.15
    if "draft" in text and plan.status == "active":
        score -= 0.05
    return round(max(0.0, min(1.0, score)), 4)


def _evidence_quality(
    evidence: Sequence[str],
    reflection: Reflection | None,
) -> float:
    if not evidence:
        base = 0.2
    else:
        base = min(0.9, 0.35 + 0.15 * len(evidence))
    if reflection is not None and any(
        "missing_evidence" in w for w in reflection.weaknesses
    ):
        base -= 0.15
    return round(max(0.0, min(1.0, base)), 4)


def _calibration(
    plan: CognitionPlan,
    evidence: Sequence[str],
    reflection: Reflection | None,
) -> float:
    # High confidence with little evidence → poor calibration.
    evidence_strength = min(1.0, len(evidence) / 4.0)
    gap = abs(plan.confidence - evidence_strength)
    score = 1.0 - gap
    if reflection is not None and reflection.assumptions:
        score -= min(0.2, 0.04 * len(reflection.assumptions))
    return round(max(0.0, min(1.0, score)), 4)
