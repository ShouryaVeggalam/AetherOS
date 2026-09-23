"""Cooldown-based cooldown tracker for recommendations.

Stops the same class of advice from being re-approved too quickly.
This is in-memory state for the running process — not OS mutation.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


# Default cool-downs keyed by recommendation category (seconds).
DEFAULT_COOLDOWNS_SECONDS: dict[str, float] = {
    "cpu": 60.0,
    "memory": 90.0,
    "disk": 300.0,
    "idle": 120.0,
    "default": 60.0,
}


def category_for_title(title: str) -> str:
    """Map a recommendation title to a cooldown category.

    Args:
        title: Policy recommendation title.

    Returns:
        One of: cpu, memory, disk, idle, or default.
    """

    lowered = title.lower()
    if "cpu" in lowered:
        return "cpu"
    if "memory" in lowered or "ram" in lowered:
        return "memory"
    if "disk" in lowered:
        return "disk"
    if "idle" in lowered:
        return "idle"
    return "default"


@dataclass
class CooldownManager:
    """Tracks last-approval times per recommendation category.

    Args:
        cooldowns_seconds: Optional override map of category → seconds.
    """

    cooldowns_seconds: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_COOLDOWNS_SECONDS)
    )
    _last_approved_at: dict[str, float] = field(default_factory=dict)

    def cooldown_seconds_for(self, title: str) -> float:
        """Return the cooldown duration for a recommendation title."""

        category = category_for_title(title)
        return self.cooldowns_seconds.get(
            category, self.cooldowns_seconds.get("default", 60.0)
        )

    def remaining_seconds(self, title: str, *, now: float | None = None) -> float:
        """Seconds left before this title's category may be approved again.

        Args:
            title: Recommendation title.
            now: Optional monotonic/timestamp override for tests.

        Returns:
            Remaining seconds (0.0 when not cooling down).
        """

        category = category_for_title(title)
        last = self._last_approved_at.get(category)
        if last is None:
            return 0.0
        clock = time.monotonic() if now is None else now
        elapsed = clock - last
        remaining = self.cooldown_seconds_for(title) - elapsed
        return max(0.0, remaining)

    def is_cooling_down(self, title: str, *, now: float | None = None) -> bool:
        """Return True if this category is still inside its cooldown window."""

        return self.remaining_seconds(title, now=now) > 0.0

    def mark_approved(self, title: str, *, now: float | None = None) -> None:
        """Record that a recommendation in this category was just approved."""

        category = category_for_title(title)
        self._last_approved_at[category] = time.monotonic() if now is None else now

    def clear(self) -> None:
        """Reset all cooldown timers (useful in tests)."""

        self._last_approved_at.clear()
