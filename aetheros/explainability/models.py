"""Explainability data contracts for AetherOS v1.2.

Immutable evidence objects only. Never invent reasons or fabricate values.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

EvidenceSource = Literal["telemetry", "history", "intent", "simulation"]


@dataclass(frozen=True, slots=True)
class Evidence:
    """One immutable, traceable fact supporting an explanation.

    Attributes:
        source: Origin category (telemetry, history, intent, simulation).
        metric: Metric or profile key this fact refers to.
        value: Numeric measurement when applicable, else 0.0.
        timestamp: When the evidence was observed or derived.
        description: Human-readable statement grounded in real data.
    """

    source: EvidenceSource
    metric: str
    value: float
    timestamp: datetime
    description: str


@dataclass(frozen=True, slots=True)
class ReasoningChain:
    """Structured reasoning steps derived only from collected evidence.

    Attributes:
        observations: Present-tense facts from current telemetry.
        historical_patterns: Trends computed from stored history.
        simulation_support: What-if outcomes from SimulationResult.
        intent_context: Active profile priorities that shaped scoring.
    """

    observations: tuple[str, ...]
    historical_patterns: tuple[str, ...]
    simulation_support: tuple[str, ...]
    intent_context: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Explanation:
    """Full evidence-based explanation for one AI decision.

    Attributes:
        title: Recommendation title being explained.
        summary: Final conclusion sentence.
        confidence: Computed confidence score 0–100.
        evidence: Traceable evidence facts (immutable).
        reasoning_chain: Ordered reasoning sections.
    """

    title: str
    summary: str
    confidence: int
    evidence: tuple[Evidence, ...]
    reasoning_chain: ReasoningChain

    def __post_init__(self) -> None:
        """Reject confidence outside 0–100."""

        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")
