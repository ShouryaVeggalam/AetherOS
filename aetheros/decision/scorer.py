"""Weighted priority scoring for approved recommendations.

Score = severity points + confidence points ± bonuses/penalties,
clamped to 0–100. Pure functions — no OS side effects.
"""

from __future__ import annotations

from aetheros.policy_engine.models import PolicyRecommendation, SeverityLevel, TelemetrySnapshot

# Severity base weights.
SEVERITY_POINTS: dict[SeverityLevel, int] = {
    "critical": 60,
    "warning": 30,
    "normal": 0,
}

# Confidence contributes up to this many points (at confidence=100).
MAX_CONFIDENCE_POINTS = 30

# Applied when this category was recently in cooldown before evaluation.
COOLDOWN_PENALTY = 20

# Applied when multiple resources look overloaded together.
OVERLOAD_BONUS = 10

# Thresholds for the system-wide overload bonus.
OVERLOAD_CPU_THRESHOLD = 85.0
OVERLOAD_MEMORY_THRESHOLD = 85.0


def confidence_points(confidence: int) -> float:
    """Convert confidence (0–100) into up to 30 score points."""

    clamped = max(0, min(100, confidence))
    return (clamped / 100.0) * MAX_CONFIDENCE_POINTS


def has_system_wide_overload(snapshot: TelemetrySnapshot) -> bool:
    """Return True when CPU and memory are both under heavy load."""

    return (
        snapshot.cpu_percent >= OVERLOAD_CPU_THRESHOLD
        and snapshot.memory_percent >= OVERLOAD_MEMORY_THRESHOLD
    )


def score_recommendation(
    recommendation: PolicyRecommendation,
    snapshot: TelemetrySnapshot,
    *,
    recently_cooled: bool = False,
) -> int:
    """Compute a priority score from 0–100 for one recommendation.

    Args:
        recommendation: Approved policy advice to score.
        snapshot: Telemetry context for overload bonus.
        recently_cooled: True when this category was cooling before
            the current evaluation cycle (applies −20).

    Returns:
        Integer priority score clamped to 0–100.
    """

    total = float(SEVERITY_POINTS[recommendation.level])
    total += confidence_points(recommendation.confidence)

    if recently_cooled:
        total -= COOLDOWN_PENALTY

    if has_system_wide_overload(snapshot):
        total += OVERLOAD_BONUS

    return int(max(0, min(100, round(total))))
