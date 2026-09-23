"""Select the single highest-priority recommendation.

Given scored candidates, the prioritizer returns one winner.
Ties break by confidence, then by severity rank.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.policy_engine.models import SEVERITY_RANK, PolicyRecommendation


@dataclass(frozen=True, slots=True)
class ScoredRecommendation:
    """A recommendation paired with its computed priority score."""

    recommendation: PolicyRecommendation
    priority_score: int


def prioritize(candidates: list[ScoredRecommendation]) -> ScoredRecommendation | None:
    """Return the highest-priority scored recommendation.

    Args:
        candidates: Scored approved recommendations.

    Returns:
        The winner, or None when the list is empty.
    """

    if not candidates:
        return None

    return max(candidates, key=_sort_key)


def _sort_key(item: ScoredRecommendation) -> tuple[int, int, int]:
    """Sort key: score, confidence, severity (all higher-is-better)."""

    rec = item.recommendation
    return (item.priority_score, rec.confidence, SEVERITY_RANK[rec.level])
