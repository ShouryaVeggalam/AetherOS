"""Confidence engine — weighted score from measurable agreement signals.

Returns 0–100. Weights are structural; no fixed confidence constants like 93.
"""

from __future__ import annotations

from aetheros.reasoning.models import ReasoningPath


def compute_confidence(
    *,
    paths: tuple[ReasoningPath, ...],
    evidence_count: int,
    historical_agreement: float,
    simulation_agreement: float,
) -> int:
    """Compute confidence from path completeness and agreement ratios.

    Args:
        paths: Verified supporting graph paths.
        evidence_count: Number of Evidence facts attached.
        historical_agreement: 0–1 fraction of history supporting the claim.
        simulation_agreement: 0–1 fraction of simulation support.

    Returns:
        Integer confidence in 0–100.
    """

    path_completeness = _path_completeness(paths)
    evidence_score = _evidence_score(evidence_count)
    hist = _clamp01(historical_agreement)
    sim = _clamp01(simulation_agreement)
    raw = (
        0.35 * path_completeness
        + 0.30 * evidence_score
        + 0.20 * hist
        + 0.15 * sim
    )
    return int(round(100 * _clamp01(raw)))


def _path_completeness(paths: tuple[ReasoningPath, ...]) -> float:
    """Average normalised depth across paths (0 if none)."""

    if not paths:
        return 0.0
    scores = [min(1.0, path.depth / 4.0) for path in paths if path.depth > 0]
    if not scores:
        return 0.0
    coverage = min(1.0, len(scores) / 3.0)
    return 0.7 * (sum(scores) / len(scores)) + 0.3 * coverage


def _evidence_score(count: int) -> float:
    """Diminishing returns on evidence cardinality."""

    if count <= 0:
        return 0.0
    return min(1.0, count / 5.0)


def _clamp01(value: float) -> float:
    """Clamp to the unit interval."""

    return max(0.0, min(1.0, value))
