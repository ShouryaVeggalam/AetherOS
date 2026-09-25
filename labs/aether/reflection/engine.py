"""Reflection Engine — identify gaps, assumptions, ambiguity, missing evidence."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from labs.aether.models.types import CognitionPlan, Reflection

_ASSUMPTION_CUES: tuple[str, ...] = (
    "assume",
    "assuming",
    "presumably",
    "should be",
    "must be",
    "obviously",
    "clearly",
)
_AMBIGUITY_CUES: tuple[str, ...] = (
    "maybe",
    "perhaps",
    "unclear",
    "ambiguous",
    "somewhat",
    "roughly",
    "approx",
)
_GAP_CUES: tuple[str, ...] = (
    "unknown",
    "missing",
    "todo",
    "not sure",
    "unverified",
    "gap",
    "incomplete",
)


def reflect_on_reasoning(
    *,
    plan: CognitionPlan,
    reasoning_summary: str,
    evidence: Sequence[str] = (),
    now: datetime | None = None,
    reflection_id: str | None = None,
) -> Reflection:
    """Produce a structured reflection from a reasoning summary + plan context."""

    text = reasoning_summary.strip()
    if not text:
        raise ValueError("reasoning_summary must be non-empty")
    stamp = now or datetime.now(UTC)
    lower = text.lower()

    assumptions = _find_cues(lower, _ASSUMPTION_CUES, label="assumption")
    weaknesses = list(_find_cues(lower, _GAP_CUES, label="logical_gap"))
    weaknesses.extend(_find_cues(lower, _AMBIGUITY_CUES, label="ambiguity"))

    if not evidence:
        weaknesses.append("missing_evidence: no evidence items supplied")
    elif len(evidence) < 2 and plan.complexity in ("complex", "strategic"):
        weaknesses.append("missing_evidence: sparse evidence for complexity tier")

    if plan.attention_budget < 0.35:
        weaknesses.append("attention_budget_low: reasoning may be under-resourced")

    if "because" not in lower and "therefore" not in lower and "so " not in lower:
        weaknesses.append("logical_gap: weak causal connective tissue")

    # Extract quoted/assumed phrases as assumptions when cue present.
    for match in re.finditer(
        r"(?:assume|assuming|presumably)\s+([^.;\n]{3,80})",
        text,
        flags=re.IGNORECASE,
    ):
        assumptions = assumptions + (f"extracted: {match.group(1).strip()}",)

    improvements = _improvements(weaknesses, assumptions, evidence)
    # Deduplicate while preserving order.
    weaknesses_t = _dedupe(tuple(weaknesses))
    assumptions_t = _dedupe(assumptions)

    return Reflection(
        id=reflection_id or f"ref_{uuid4().hex[:12]}",
        reasoning_summary=text,
        weaknesses=weaknesses_t,
        assumptions=assumptions_t,
        improvements=improvements,
        plan_id=plan.id,
        created_at=stamp,
    )


def _find_cues(
    text: str,
    cues: Sequence[str],
    *,
    label: str,
) -> tuple[str, ...]:
    hits: list[str] = []
    for cue in cues:
        if cue in text:
            hits.append(f"{label}: contains '{cue}'")
    return tuple(hits)


def _improvements(
    weaknesses: Sequence[str],
    assumptions: Sequence[str],
    evidence: Sequence[str],
) -> tuple[str, ...]:
    items: list[str] = []
    if any("missing_evidence" in w for w in weaknesses):
        items.append("Collect and cite additional verified evidence")
    if any("ambiguity" in w for w in weaknesses):
        items.append("Replace ambiguous language with measurable criteria")
    if any("logical_gap" in w for w in weaknesses):
        items.append("Add explicit causal steps (because → therefore)")
    if assumptions:
        items.append("Surface and test unsupported assumptions explicitly")
    if len(evidence) >= 2 and not items:
        items.append("Tighten confidence calibration against evidence strength")
    if not items:
        items.append("Re-run verification against plan constraints")
    return tuple(items[:6])


def _dedupe(items: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return tuple(out)
