"""Decision-engine data contracts.

A Decision is the single prioritized outcome chosen from approved
policy recommendations. It is advice only — never an OS command.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

SeverityLevel = Literal["normal", "warning", "critical"]


@dataclass(frozen=True, slots=True)
class Decision:
    """One prioritized system decision produced by the decision engine.

    Attributes:
        title: Short label (usually from the winning recommendation).
        severity: normal, warning, or critical.
        confidence: Confidence inherited from the policy rule (0–100).
        priority_score: Weighted score from 0–100.
        explanation: Human-readable justification for this choice.
        action: Recommended operator action (text only, never executed).
        timestamp: UTC time when the decision was produced.
    """

    title: str
    severity: SeverityLevel
    confidence: int
    priority_score: int
    explanation: str
    action: str
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate score and confidence bounds."""

        if not 0 <= self.priority_score <= 100:
            raise ValueError("priority_score must be between 0 and 100")
        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""

    return datetime.now(UTC)
