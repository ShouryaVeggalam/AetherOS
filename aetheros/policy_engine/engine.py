"""PolicyEngine: run all rules against one telemetry snapshot.

This class only evaluates and returns recommendations.
It never executes actions or talks to the OS beyond reading the snapshot.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from aetheros.policy_engine.models import (
    SEVERITY_RANK,
    PolicyRecommendation,
    TelemetrySnapshot,
)
from aetheros.policy_engine.rules import (
    detect_cpu_overload,
    detect_disk_pressure,
    detect_idle_state,
    detect_memory_pressure,
)

RuleFn = Callable[[TelemetrySnapshot], PolicyRecommendation | None]

DEFAULT_RULES: tuple[RuleFn, ...] = (
    detect_cpu_overload,
    detect_memory_pressure,
    detect_disk_pressure,
    detect_idle_state,
)


class PolicyEngine:
    """Evaluates telemetry and produces sorted recommendations.

    Args:
        rules: Optional custom rule list. Defaults to the Phase-2 detectors.
    """

    def __init__(self, rules: Sequence[RuleFn] | None = None) -> None:
        """Store the rule pipeline used by evaluate / evaluate_all."""

        self._rules: tuple[RuleFn, ...] = tuple(rules) if rules is not None else DEFAULT_RULES

    def evaluate(self, snapshot: TelemetrySnapshot) -> PolicyRecommendation | None:
        """Return the single most severe recommendation, if any.

        Args:
            snapshot: Flat telemetry sample to evaluate.

        Returns:
            The highest-severity recommendation, or None when every rule
            returns None (truly nothing to say — rarer than "healthy").
        """

        recommendations = self.evaluate_all(snapshot)
        return recommendations[0] if recommendations else None

    def evaluate_all(self, snapshot: TelemetrySnapshot) -> list[PolicyRecommendation]:
        """Run every rule and return recommendations sorted by severity.

        Critical comes first, then warning, then normal (e.g. idle).
        Within the same level, higher confidence ranks first.

        Args:
            snapshot: Flat telemetry sample to evaluate.

        Returns:
            A list of PolicyRecommendation values (may be empty).
        """

        found: list[PolicyRecommendation] = []
        for rule in self._rules:
            result = rule(snapshot)
            if result is not None:
                found.append(result)

        found.sort(
            key=lambda item: (SEVERITY_RANK[item.level], item.confidence),
            reverse=True,
        )
        return found
