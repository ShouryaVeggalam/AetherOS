"""Research-engine data contracts.

All structures are immutable advice artifacts. Nothing here executes
commands or changes the host operating system.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aetheros.intent.models import IntentProfile
from aetheros.learning.models import HistoricalPattern
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.simulation.models import SimulationResult


@dataclass(frozen=True, slots=True)
class CandidateStrategy:
    """One generated optimization strategy (advice only).

    Attributes:
        title: Short strategy name.
        description: What the strategy aims to achieve.
        expected_cpu_delta: Expected change in CPU % (negative = relief).
        expected_memory_delta: Expected change in memory %.
        expected_efficiency_delta: Expected efficiency gain (higher = better).
    """

    title: str
    description: str
    expected_cpu_delta: float
    expected_memory_delta: float
    expected_efficiency_delta: float


@dataclass(frozen=True, slots=True)
class EvaluatedStrategy:
    """A candidate paired with its immutable simulation result."""

    strategy: CandidateStrategy
    simulation: SimulationResult


@dataclass(frozen=True, slots=True)
class RankedStrategy:
    """An evaluated strategy with a final weighted rank score."""

    rank: int
    strategy: CandidateStrategy
    simulation: SimulationResult
    rank_score: float
    reason: str


@dataclass(frozen=True, slots=True)
class ResearchReport:
    """Full autonomous research outcome ready for markdown export.

    Attributes:
        created_at: UTC timestamp when research completed.
        snapshot: Telemetry used as input.
        intent: Active intent profile.
        patterns: Historical patterns considered.
        candidates: Generated strategies.
        ranked: Ranked evaluation results (best first).
        winner: Top ranked strategy, if any.
        report_path: Path to the written markdown file, if saved.
    """

    created_at: datetime
    snapshot: TelemetrySnapshot
    intent: IntentProfile
    patterns: tuple[HistoricalPattern, ...]
    candidates: tuple[CandidateStrategy, ...]
    ranked: tuple[RankedStrategy, ...]
    winner: RankedStrategy | None
    report_path: str | None = None
