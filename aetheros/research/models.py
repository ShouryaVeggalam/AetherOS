"""Research-engine data contracts.

All structures are immutable advice artifacts. Nothing here executes
commands or changes the host operating system.

Strategy research (autonomous generate→simulate→rank) uses
``CandidateStrategy`` / ``ResearchReport``.

P9 Research Intelligence (evidence reports) uses
``ResearchObservation`` / ``SystemResearchReport`` and related types.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from aetheros.intent.models import IntentProfile
from aetheros.learning.models import HistoricalPattern
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.simulation.models import SimulationResult

TrendDirection = Literal["rising", "falling", "stable", "insufficient_data"]
TrendWindow = Literal["last_hour", "today", "7_days", "30_days"]
TrendMetric = Literal[
    "cpu",
    "memory",
    "disk",
    "battery",
    "network",
    "cluster_health",
]
BottleneckKind = Literal[
    "disk_contention",
    "memory_pressure",
    "foreground_cpu_saturation",
    "network_congestion",
]
ReportKind = Literal["daily", "weekly", "research_summary", "simulation_summary"]


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


@dataclass(frozen=True, slots=True)
class ResearchObservation:
    """One evidence-backed finding from graph / telemetry / reasoning.

    Attributes:
        id: Stable observation identifier.
        timestamp: When the observation was minted (UTC).
        title: Operator-facing claim (must be grounded in ``evidence``).
        metric: Metric key the claim refers to (e.g. ``cpu``).
        value: Numeric magnitude supporting the claim.
        evidence: Immutable evidence strings (paths, deltas, counts).
    """

    id: str
    timestamp: datetime
    title: str
    metric: str
    value: float
    evidence: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.title.strip():
            raise ValueError("title must be non-empty")
        if not self.evidence:
            raise ValueError("observation requires at least one evidence item")


@dataclass(frozen=True, slots=True)
class TrendAnalysis:
    """Directional trend for one metric over a fixed window.

    Attributes:
        metric: Tracked metric key.
        window: Analysis window label.
        direction: rising / falling / stable / insufficient_data.
        confidence: Confidence 0–100 grounded in sample count + magnitude.
    """

    metric: TrendMetric
    window: TrendWindow
    direction: TrendDirection
    confidence: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class BottleneckFinding:
    """Recurring bottleneck with supporting resource-graph paths."""

    kind: BottleneckKind
    title: str
    summary: str
    graph_paths: tuple[str, ...]
    evidence_count: int
    confidence: float

    def __post_init__(self) -> None:
        if not self.graph_paths:
            raise ValueError("bottleneck requires supporting graph paths")
        if self.evidence_count < 1:
            raise ValueError("bottleneck requires evidence_count >= 1")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class Discovery:
    """Verified research discovery — never emitted without evidence gates.

    Attributes:
        title: Discovery headline.
        summary: Short evidence-backed narrative.
        evidence_count: Number of supporting sessions/samples.
        confidence: Overall confidence 0–100.
        supporting_reasoning: Verified reasoning statements.
        simulation_agreement: Optional twin/simulation agreement 0–100.
    """

    title: str
    summary: str
    evidence_count: int
    confidence: float
    supporting_reasoning: tuple[str, ...]
    simulation_agreement: float | None = None

    def __post_init__(self) -> None:
        if self.evidence_count < 1:
            raise ValueError("discovery requires evidence_count >= 1")
        if not self.supporting_reasoning:
            raise ValueError("discovery requires verified supporting_reasoning")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")
        if self.simulation_agreement is not None and not (
            0.0 <= self.simulation_agreement <= 100.0
        ):
            raise ValueError("simulation_agreement must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class SystemResearchReport:
    """P9 Research Intelligence publishable report (evidence only).

    Distinct from strategy ``ResearchReport`` (generate→rank strategies).

    Attributes:
        id: Report identifier.
        generated_at: UTC generation time.
        context: Intent / operational context label.
        observations: Evidence-backed observations.
        trends: Trend analyses.
        bottlenecks: Bottleneck findings with graph paths.
        discoveries: Gate-verified discoveries only.
        simulations: Simulation evidence summaries.
        conclusion: Closing research-grade statement.
        kind: daily / weekly / research_summary / simulation_summary.
    """

    id: str
    generated_at: datetime
    context: str
    observations: tuple[ResearchObservation, ...]
    trends: tuple[TrendAnalysis, ...]
    bottlenecks: tuple[BottleneckFinding, ...]
    discoveries: tuple[Discovery, ...]
    simulations: tuple[str, ...]
    conclusion: str
    kind: ReportKind = "research_summary"

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.conclusion.strip():
            raise ValueError("conclusion must be non-empty")
