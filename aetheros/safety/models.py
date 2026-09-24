"""Safety-layer data contracts.

SafetyResult records whether a recommendation was allowed through.
It never carries executable commands — only a decision and a reason.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

SafetyStatus = Literal["approved", "blocked", "cooldown"]


@dataclass(frozen=True, slots=True)
class SafetyResult:
    """Outcome of validating one policy recommendation.

    Attributes:
        approved: True only when status is "approved".
        status: approved, blocked, or cooldown.
        reason: Human-readable explanation of the decision.
        timestamp: UTC time when the decision was made.
    """

    approved: bool
    status: SafetyStatus
    reason: str
    timestamp: datetime

    def __post_init__(self) -> None:
        """Keep approved flag consistent with status."""

        if self.status == "approved" and not self.approved:
            raise ValueError("status 'approved' requires approved=True")
        if self.status != "approved" and self.approved:
            raise ValueError("approved=True is only valid with status 'approved'")


def utc_now() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""

    return datetime.now(UTC)


def make_approved(reason: str) -> SafetyResult:
    """Build an approved SafetyResult with a fresh timestamp."""

    return SafetyResult(
        approved=True,
        status="approved",
        reason=reason,
        timestamp=utc_now(),
    )


def make_blocked(reason: str) -> SafetyResult:
    """Build a blocked SafetyResult with a fresh timestamp."""

    return SafetyResult(
        approved=False,
        status="blocked",
        reason=reason,
        timestamp=utc_now(),
    )


def make_cooldown(reason: str) -> SafetyResult:
    """Build a cooldown SafetyResult with a fresh timestamp."""

    return SafetyResult(
        approved=False,
        status="cooldown",
        reason=reason,
        timestamp=utc_now(),
    )
