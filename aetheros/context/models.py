"""Context Intelligence Engine models — immutable operational state.

``aetheros.context.GraphContext`` is the P8 operational context aggregate.
Distinct from the lighter ``aetheros.bridge.GraphContext`` (graph-only view).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

IntentName = Literal[
    "CODING",
    "AI",
    "GAMING",
    "EDITING",
    "BATTERY",
    "BALANCED",
]

IntentSource = Literal["manual", "foreground", "history", "combined"]


@dataclass(frozen=True, slots=True)
class IntentContext:
    """Resolved operator intent with provenance.

    Attributes:
        name: Canonical intent key (CODING / AI / …).
        confidence: Resolver confidence 0–100.
        source: How the intent was derived.
        duration: Seconds the intent has been considered active (0 if unknown).
    """

    name: IntentName
    confidence: int
    source: IntentSource
    duration: float

    def __post_init__(self) -> None:
        """Reject invalid confidence / duration."""

        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")
        if self.duration < 0:
            raise ValueError("duration must be non-negative")


@dataclass(frozen=True, slots=True)
class HistoricalPattern:
    """One matched historical situation from observatory telemetry.

    Attributes:
        label: Operator-facing pattern name.
        similarity: Match score 0–100.
        evidence_count: Number of supporting historical samples/sessions.
    """

    label: str
    similarity: float
    evidence_count: int

    def __post_init__(self) -> None:
        """Reject invalid similarity / counts."""

        if not 0.0 <= self.similarity <= 100.0:
            raise ValueError("similarity must be in [0, 100]")
        if self.evidence_count < 0:
            raise ValueError("evidence_count must be non-negative")


@dataclass(frozen=True, slots=True)
class GraphContext:
    """Single immutable operational context for all intelligence subsystems.

    Attributes:
        timestamp: Context materialisation time (UTC).
        active_intent: Resolved intent context.
        foreground_process: Dominant process name, or None.
        cpu_load: Current CPU percent 0–100.
        memory_load: Current memory percent 0–100.
        disk_load: Current disk percent 0–100.
        battery_state: Human-readable battery status (e.g. ``Charging 80%``).
        cluster_health: Aggregate cluster health label.
        simulation_state: ``active`` / ``idle``.
        historical_pattern: Best history match, or None when evidence is weak.
        confidence: Overall context confidence 0–100.
    """

    timestamp: datetime
    active_intent: IntentContext
    foreground_process: str | None
    cpu_load: float
    memory_load: float
    disk_load: float
    battery_state: str
    cluster_health: str
    simulation_state: str
    historical_pattern: HistoricalPattern | None
    confidence: int

    def __post_init__(self) -> None:
        """Reject invalid loads / confidence."""

        for label, value in (
            ("cpu_load", self.cpu_load),
            ("memory_load", self.memory_load),
            ("disk_load", self.disk_load),
        ):
            if not 0.0 <= value <= 100.0:
                raise ValueError(f"{label} must be in [0, 100]")
        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")
