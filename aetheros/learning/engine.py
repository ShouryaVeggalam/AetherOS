"""Minimal Learning Engine — surface historical patterns for research.

Reads past safety-audit rows when available; otherwise returns safe
built-in defaults. Never executes OS commands.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from aetheros.learning.models import HistoricalPattern
from aetheros.safety.audit import AuditLogger


@dataclass
class LearningEngine:
    """Provide historical patterns for the research pipeline.

    Args:
        audit: Optional audit logger used to derive simple trends.
    """

    audit: AuditLogger = field(
        default_factory=lambda: AuditLogger(Path("data/safety_audit.db"))
    )

    def get_patterns(self) -> tuple[HistoricalPattern, ...]:
        """Return historical patterns (audit-derived + defaults)."""

        patterns: list[HistoricalPattern] = [
            HistoricalPattern(
                name="Background CPU Spikes",
                description="Past sessions often show background CPU contention.",
                cpu_bias=20.0,
                memory_bias=5.0,
                confidence=70,
            ),
            HistoricalPattern(
                name="Interactive Latency Sensitivity",
                description="User intents like Coding benefit from lower latency.",
                cpu_bias=10.0,
                memory_bias=0.0,
                confidence=75,
            ),
        ]
        latest = self.audit.latest()
        if latest is not None and not bool(latest["approved"]):
            patterns.append(
                HistoricalPattern(
                    name="Recent Safety Blocks",
                    description=f"Last audit blocked '{latest['title']}'.",
                    cpu_bias=5.0,
                    memory_bias=5.0,
                    confidence=60,
                )
            )
        return tuple(patterns)
