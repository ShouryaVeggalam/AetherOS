"""Complexity estimation from structural evidence only."""

from __future__ import annotations

from collections.abc import Sequence

from services.intelligence.models.types import (
    ComplexityEstimate,
    ComplexityTier,
    ObjectiveNode,
)


def estimate_complexity(
    objectives: Sequence[ObjectiveNode],
    *,
    constraint_count: int,
    context_keys: int,
    agent_count: int,
    knowledge_count: int,
) -> ComplexityEstimate:
    """Score complexity in [0, 1] and assign a tier label."""

    max_depth = max((o.depth for o in objectives), default=0)
    breadth = len(objectives)
    factors: list[str] = []

    depth_score = min(1.0, max_depth / 3.0)
    breadth_score = min(1.0, (breadth - 1) / 8.0) if breadth > 1 else 0.0
    constraint_score = min(1.0, constraint_count / 5.0)
    context_score = min(1.0, context_keys / 8.0)
    resource_score = min(1.0, (agent_count + knowledge_count) / 8.0)

    if max_depth >= 2:
        factors.append(f"decomposition_depth={max_depth}")
    if breadth >= 4:
        factors.append(f"objective_breadth={breadth}")
    if constraint_count:
        factors.append(f"constraints={constraint_count}")
    if context_keys:
        factors.append(f"context_keys={context_keys}")
    if agent_count or knowledge_count:
        factors.append(f"resources={agent_count + knowledge_count}")

    score = round(
        0.30 * depth_score
        + 0.25 * breadth_score
        + 0.20 * constraint_score
        + 0.15 * context_score
        + 0.10 * resource_score,
        4,
    )
    score = max(0.0, min(1.0, score))
    tier = _tier_for(score)
    if not factors:
        factors.append("single_objective")
    return ComplexityEstimate(score=score, tier=tier, factors=tuple(factors))


def _tier_for(score: float) -> ComplexityTier:
    if score < 0.20:
        return "trivial"
    if score < 0.45:
        return "moderate"
    if score < 0.75:
        return "complex"
    return "strategic"
