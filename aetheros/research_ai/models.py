"""Autonomous Research Engine models — twin-only scientific contracts.

Frozen dataclasses for questions, hypotheses, experiments, results, and
discoveries. Never stores personal content. Never represents live OS actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

DiscoveryStatus = Literal["verified", "rejected", "pending"]
ExperimentOutcome = Literal["supported", "rejected", "inconclusive"]


@dataclass(frozen=True, slots=True)
class ResearchQuestion:
    """One deterministic research question grounded in existing evidence."""

    id: str
    title: str
    objective: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.title.strip():
            raise ValueError("title must be non-empty")
        if not self.objective.strip():
            raise ValueError("objective must be non-empty")


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """Testable statement derived from a research question."""

    id: str
    statement: str
    rationale: str
    expected_outcome: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.statement.strip():
            raise ValueError("statement must be non-empty")
        if not self.rationale.strip():
            raise ValueError("rationale must be non-empty")
        if not self.expected_outcome.strip():
            raise ValueError("expected_outcome must be non-empty")


@dataclass(frozen=True, slots=True)
class Experiment:
    """Digital Twin experiment plan — never executed on live hosts."""

    id: str
    hypothesis: Hypothesis
    scenario: str
    iterations: int
    snapshot_id: str
    variables: tuple[tuple[str, str], ...] = ()
    metrics: tuple[str, ...] = ("cpu", "memory", "disk", "stability")

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if self.iterations < 1:
            raise ValueError("iterations must be >= 1")
        if not self.scenario.strip():
            raise ValueError("scenario must be non-empty")
        if not self.snapshot_id.strip():
            raise ValueError("snapshot_id must be non-empty")


@dataclass(frozen=True, slots=True)
class Result:
    """Aggregated twin-run metrics for one experiment."""

    metrics: tuple[tuple[str, float], ...]
    stability: float
    confidence: float
    evidence: tuple[str, ...]
    successful_iterations: int
    total_iterations: int

    def __post_init__(self) -> None:
        if not 0.0 <= self.stability <= 100.0:
            raise ValueError("stability must be in [0, 100]")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")
        if self.total_iterations < 1:
            raise ValueError("total_iterations must be >= 1")
        if not 0 <= self.successful_iterations <= self.total_iterations:
            raise ValueError("successful_iterations out of range")

    @property
    def reproducibility(self) -> float:
        """Successful iteration ratio as a percent 0–100."""

        return round(100.0 * self.successful_iterations / self.total_iterations, 2)


@dataclass(frozen=True, slots=True)
class Discovery:
    """Verified (or rejected) research discovery from twin experiments."""

    title: str
    summary: str
    reproducibility: float
    evidence_count: int
    confidence: float
    status: DiscoveryStatus = "verified"
    question_id: str = ""
    experiment_id: str = ""

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must be non-empty")
        if not self.summary.strip():
            raise ValueError("summary must be non-empty")
        if not 0.0 <= self.reproducibility <= 100.0:
            raise ValueError("reproducibility must be in [0, 100]")
        if self.evidence_count < 1:
            raise ValueError("evidence_count must be >= 1")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class JournalEntry:
    """Append-only research journal record."""

    experiment_id: str
    hypothesis_id: str
    timestamp: datetime
    outcome: ExperimentOutcome
    reproducibility: float
    note: str = ""

    def __post_init__(self) -> None:
        if not self.experiment_id.strip():
            raise ValueError("experiment_id must be non-empty")
        if not self.hypothesis_id.strip():
            raise ValueError("hypothesis_id must be non-empty")
        if not 0.0 <= self.reproducibility <= 100.0:
            raise ValueError("reproducibility must be in [0, 100]")
