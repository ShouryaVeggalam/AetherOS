"""Learning-engine data contracts (minimal Phase 7 support).

Historical patterns are observational summaries — never OS mutations.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HistoricalPattern:
    """A learned tendency from past telemetry / audit observations.

    Attributes:
        name: Short pattern label.
        description: Human-readable summary.
        cpu_bias: Typical CPU pressure signal (−100…100).
        memory_bias: Typical memory pressure signal (−100…100).
        confidence: How strongly this pattern should influence research (0–100).
    """

    name: str
    description: str
    cpu_bias: float
    memory_bias: float
    confidence: int
