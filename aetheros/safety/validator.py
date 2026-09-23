"""SafetyValidator: gate every policy recommendation.

Checks confidence, banned phrases, contradictions, and cooldowns.
Approving means "safe to surface" — never "execute on the OS".
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from aetheros.policy_engine.models import PolicyRecommendation
from aetheros.safety.audit import AuditLogger
from aetheros.safety.cooldown import CooldownManager
from aetheros.safety.models import (
    SafetyResult,
    make_approved,
    make_blocked,
    make_cooldown,
)

# Phrases that must never appear in recommendation text.
BANNED_PATTERNS: tuple[str, ...] = (
    "kill",
    "sudo",
    "terminate",
    "rm",
    "chmod",
    "os.system",
    "subprocess",
)

# Critical advice below this confidence is rejected.
MIN_CRITICAL_CONFIDENCE = 80

_WORD_BOUNDARY = r"(?<![a-z0-9_.]){token}(?![a-z0-9_.])"


@dataclass
class SafetyValidator:
    """Validate recommendations and record every decision.

    Args:
        cooldown: Tracks per-category approval cool-downs.
        audit: Append-only SQLite logger.
    """

    cooldown: CooldownManager = field(default_factory=CooldownManager)
    audit: AuditLogger = field(
        default_factory=lambda: AuditLogger(Path("data/safety_audit.db"))
    )

    def validate(
        self,
        recommendation: PolicyRecommendation,
        *,
        batch: Sequence[PolicyRecommendation] | None = None,
        record: bool = True,
    ) -> SafetyResult:
        """Validate one recommendation and optionally audit the outcome.

        Args:
            recommendation: Advice from the policy engine.
            batch: Sibling recommendations used for contradiction checks.
            record: When True, write the decision to the audit log and,
                if approved, start the category cooldown.

        Returns:
            A SafetyResult describing approved / blocked / cooldown.
        """

        result = self._check(recommendation, batch=batch or ())
        if record:
            self.audit.log(recommendation, result)
            if result.approved:
                self.cooldown.mark_approved(recommendation.title)
        return result

    def validate_all(
        self,
        recommendations: Sequence[PolicyRecommendation],
        *,
        record: bool = True,
    ) -> list[tuple[PolicyRecommendation, SafetyResult]]:
        """Validate every recommendation in a batch.

        Args:
            recommendations: Policy advice list from one evaluation.
            record: Whether to audit and update cooldowns.

        Returns:
            Pairs of (recommendation, SafetyResult) in input order.
        """

        return [
            (rec, self.validate(rec, batch=recommendations, record=record))
            for rec in recommendations
        ]

    def _check(
        self,
        recommendation: PolicyRecommendation,
        *,
        batch: Sequence[PolicyRecommendation],
    ) -> SafetyResult:
        """Apply all safety rules; return the first failure or approval."""

        banned = _find_banned_phrase(recommendation)
        if banned is not None:
            return make_blocked(
                f"Rejected unsafe phrase in recommendation text: '{banned}'."
            )

        if (
            recommendation.level == "critical"
            and recommendation.confidence < MIN_CRITICAL_CONFIDENCE
        ):
            return make_blocked(
                f"Critical actions require confidence >= {MIN_CRITICAL_CONFIDENCE} "
                f"(got {recommendation.confidence})."
            )

        if _contradicts_batch(recommendation, batch):
            return make_blocked(
                "Contradictory recommendations in the same batch "
                "(idle vs resource pressure)."
            )

        remaining = self.cooldown.remaining_seconds(recommendation.title)
        if remaining > 0:
            return make_cooldown(
                f"Duplicate recommendation during cooldown "
                f"({remaining:.0f}s remaining)."
            )

        return make_approved(
            f"Confidence {recommendation.confidence}%, cooldown passed."
        )


def _recommendation_text(recommendation: PolicyRecommendation) -> str:
    """Concatenate searchable fields from a recommendation."""

    return " ".join(
        [
            recommendation.title,
            recommendation.reason,
            recommendation.recommended_action,
        ]
    ).lower()


def _find_banned_phrase(recommendation: PolicyRecommendation) -> str | None:
    """Return the first banned token found, or None if clean.

    Uses word-boundary matching so 'chmod' matches but we still catch
    short tokens like 'rm' without needing a full shell parser.
    """

    text = _recommendation_text(recommendation)
    for token in BANNED_PATTERNS:
        pattern = _WORD_BOUNDARY.format(token=re.escape(token.lower()))
        if re.search(pattern, text, flags=re.IGNORECASE):
            return token
    return None


def _is_idle(recommendation: PolicyRecommendation) -> bool:
    """Return True if this recommendation describes an idle system."""

    return "idle" in recommendation.title.lower()


def _is_pressure(recommendation: PolicyRecommendation) -> bool:
    """Return True if this recommendation describes resource pressure."""

    title = recommendation.title.lower()
    markers = ("cpu", "memory", "disk", "overload", "pressure")
    return any(marker in title for marker in markers) and not _is_idle(recommendation)


def _contradicts_batch(
    recommendation: PolicyRecommendation,
    batch: Sequence[PolicyRecommendation],
) -> bool:
    """Detect idle + resource-pressure contradictions in one batch.

    When both appear, the idle recommendation is rejected so real
    pressure alerts can still be considered.
    """

    if not batch or not _is_idle(recommendation):
        return False
    return any(_is_pressure(item) for item in batch)
