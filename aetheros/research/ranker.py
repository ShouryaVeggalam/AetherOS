"""Rank evaluated strategies with fixed performance/stability/efficiency weights."""

from __future__ import annotations

from collections.abc import Sequence

from aetheros.research.models import EvaluatedStrategy, RankedStrategy

PERFORMANCE_WEIGHT = 0.40
STABILITY_WEIGHT = 0.35
EFFICIENCY_WEIGHT = 0.25


def rank_strategies(
    evaluated: Sequence[EvaluatedStrategy],
) -> tuple[RankedStrategy, ...]:
    """Return strategies sorted by weighted rank score (best first).

    Weights:
        Performance 40%, Stability 35%, Efficiency 25%.

    Args:
        evaluated: Simulation results for each candidate.

    Returns:
        Immutable ranked tuple with 1-based ranks.
    """

    scored: list[tuple[float, EvaluatedStrategy, str]] = []
    for item in evaluated:
        sim = item.simulation
        score = (
            sim.performance_score * PERFORMANCE_WEIGHT
            + sim.stability_score * STABILITY_WEIGHT
            + sim.efficiency_score * EFFICIENCY_WEIGHT
        )
        reason = _explain(item, score)
        scored.append((round(score, 1), item, reason))

    scored.sort(key=lambda row: row[0], reverse=True)

    ranked: list[RankedStrategy] = []
    for index, (score, item, reason) in enumerate(scored, start=1):
        ranked.append(
            RankedStrategy(
                rank=index,
                strategy=item.strategy,
                simulation=item.simulation,
                rank_score=score,
                reason=reason,
            )
        )
    return tuple(ranked)


def _explain(item: EvaluatedStrategy, score: float) -> str:
    """Build a short reason string for why this strategy ranked as it did."""

    sim = item.simulation
    dominant = max(
        (
            ("performance", sim.performance_score),
            ("stability", sim.stability_score),
            ("efficiency", sim.efficiency_score),
        ),
        key=lambda pair: pair[1],
    )[0]
    if dominant == "stability":
        return (
            f"Highest stability while preserving responsiveness "
            f"(score {score:.0f})."
        )
    if dominant == "efficiency":
        return f"Strong efficiency profile with solid overall score ({score:.0f})."
    return f"Strong performance outlook with overall score {score:.0f}."
