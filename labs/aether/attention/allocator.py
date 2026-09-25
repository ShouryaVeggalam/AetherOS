"""Adaptive attention allocator — deterministic budget and channel weights.

Research posture: allocate scarce cognitive resources across focus, memory
retrieval, exploration, and verification based on complexity, context
availability, memory relevance, and uncertainty.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from labs.aether.models.types import (
    AttentionAllocation,
    AttentionChannel,
    AttentionSignals,
)


def allocate_attention(
    signals: AttentionSignals,
    *,
    goal_id: str,
    now: datetime | None = None,
    allocation_id: str | None = None,
) -> AttentionAllocation:
    """Compute explainable attention weights and reasoning/retrieval budgets.

    Rules (deterministic):
    - Higher complexity → more focus + reasoning budget
    - Higher uncertainty → more verification + exploration
    - Higher memory relevance → more memory channel + retrieval budget
    - Lower available context → more retrieval, less deep focus until filled
    """

    stamp = now or datetime.now(UTC)
    raw = _raw_weights(signals)
    weights = _normalize(raw)
    reasoning = _reasoning_budget(signals)
    retrieval = _retrieval_budget(signals)
    factors = _factors(signals, weights, reasoning, retrieval)
    confidence = _confidence(signals)

    return AttentionAllocation(
        id=allocation_id or f"attn_{uuid4().hex[:12]}",
        goal_id=goal_id,
        signals=signals,
        weights=weights,
        reasoning_budget=reasoning,
        retrieval_budget=retrieval,
        factors=factors,
        confidence=confidence,
        created_at=stamp,
    )


def _raw_weights(signals: AttentionSignals) -> dict[AttentionChannel, float]:
    # Base priors — slight preference for focus under balanced conditions.
    focus = 0.28 + 0.35 * signals.task_complexity + 0.15 * signals.available_context
    memory = 0.18 + 0.45 * signals.memory_relevance
    exploration = 0.15 + 0.4 * signals.uncertainty + 0.1 * (
        1.0 - signals.available_context
    )
    verification = 0.2 + 0.35 * signals.uncertainty + 0.15 * signals.task_complexity

    # When context is scarce, shift mass from focus → memory/exploration.
    scarcity = 1.0 - signals.available_context
    focus -= 0.2 * scarcity
    memory += 0.1 * scarcity
    exploration += 0.1 * scarcity

    return {
        "focus": max(0.01, focus),
        "memory": max(0.01, memory),
        "exploration": max(0.01, exploration),
        "verification": max(0.01, verification),
    }


def _normalize(
    raw: dict[AttentionChannel, float],
) -> dict[AttentionChannel, float]:
    total = sum(raw.values())
    if total <= 0:
        equal = 0.25
        return {
            "focus": equal,
            "memory": equal,
            "exploration": equal,
            "verification": equal,
        }
    order: tuple[AttentionChannel, ...] = (
        "focus",
        "memory",
        "exploration",
        "verification",
    )
    rounded = {k: round(raw[k] / total, 6) for k in order}
    # Absorb residual rounding error into the last channel.
    residual = round(1.0 - sum(rounded[k] for k in order[:-1]), 6)
    rounded[order[-1]] = residual
    return rounded


def _reasoning_budget(signals: AttentionSignals) -> float:
    raw = (
        0.2
        + 0.45 * signals.task_complexity
        + 0.2 * signals.uncertainty
        + 0.15 * signals.available_context
        - 0.1 * (1.0 - signals.memory_relevance) * 0.5
    )
    return round(max(0.05, min(1.0, raw)), 4)


def _retrieval_budget(signals: AttentionSignals) -> float:
    raw = (
        0.15
        + 0.5 * signals.memory_relevance
        + 0.25 * (1.0 - signals.available_context)
        + 0.1 * signals.uncertainty
    )
    return round(max(0.05, min(1.0, raw)), 4)


def _confidence(signals: AttentionSignals) -> float:
    # Confidence rises with context + memory, falls with uncertainty.
    raw = (
        0.35
        + 0.3 * signals.available_context
        + 0.25 * signals.memory_relevance
        - 0.25 * signals.uncertainty
        + 0.1 * (1.0 - abs(signals.task_complexity - 0.5))
    )
    return round(max(0.05, min(0.99, raw)), 4)


def _factors(
    signals: AttentionSignals,
    weights: dict[AttentionChannel, float],
    reasoning: float,
    retrieval: float,
) -> tuple[str, ...]:
    factors: list[str] = [
        f"complexity={signals.task_complexity:.2f}",
        f"context={signals.available_context:.2f}",
        f"memory={signals.memory_relevance:.2f}",
        f"uncertainty={signals.uncertainty:.2f}",
        f"reasoning_budget={reasoning:.2f}",
        f"retrieval_budget={retrieval:.2f}",
    ]
    dominant = max(weights, key=weights.get)  # type: ignore[arg-type]
    factors.append(f"dominant_channel={dominant}:{weights[dominant]:.2f}")
    if signals.uncertainty >= 0.6:
        factors.append("high_uncertainty→boost_verification")
    if signals.available_context <= 0.35:
        factors.append("scarce_context→boost_retrieval")
    if signals.task_complexity >= 0.65:
        factors.append("high_complexity→boost_reasoning")
    return tuple(factors)
