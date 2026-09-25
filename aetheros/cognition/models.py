"""v3 Cognition Core models — immutable evidence-backed understanding.

Distinct from legacy ``aetheros.cognition.hypotheses.Hypothesis`` used by
``CognitiveRuntime``. This module is the isolated Intelligence-layer contract
for ``CognitionEngine`` (observe → reason → verify → plan).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

EvidenceSource = Literal[
    "resource_graph",
    "graph_context",
    "telemetry_history",
    "digital_twin",
    "operational_memory",
]
PlanKind = Literal["performance", "efficiency", "balanced"]


@dataclass(frozen=True, slots=True)
class Evidence:
    """One atomic, timestamped measurement or graph fact.

    Attributes:
        id: Stable evidence identifier.
        source: Provenance channel.
        metric: Metric or claim key (e.g. ``cpu``, ``path:process→cpu``).
        value: Numeric magnitude supporting the claim.
        timestamp: When the evidence was observed (UTC).
    """

    id: str
    source: EvidenceSource
    metric: str
    value: float
    timestamp: datetime

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("evidence id must be non-empty")
        if not self.metric.strip():
            raise ValueError("metric must be non-empty")


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """Candidate operational explanation grounded in evidence ids.

    v3 Cognition Core hypothesis (not the legacy hypotheses.Hypothesis).
    """

    id: str
    title: str
    description: str
    supporting_evidence: tuple[str, ...]
    confidence: float

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("hypothesis id must be non-empty")
        if not self.title.strip():
            raise ValueError("title must be non-empty")
        if not self.supporting_evidence:
            raise ValueError("hypothesis requires supporting_evidence")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class VerifiedCoreExplanation:
    """Accepted hypothesis after graph + history + simulation gates."""

    hypothesis: Hypothesis
    graph_support: bool
    historical_support: bool
    simulation_agreement: float | None
    reasons: tuple[str, ...]
    confidence: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")
        if self.simulation_agreement is not None and not (
            0.0 <= self.simulation_agreement <= 100.0
        ):
            raise ValueError("simulation_agreement must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class CognitionPlan:
    """Simulation-backed recommendation plan — never executes."""

    kind: PlanKind
    title: str
    summary: str
    steps: tuple[str, ...]
    simulation_backed: bool
    confidence: float

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError("plan requires at least one step")
        if not self.simulation_backed:
            raise ValueError("cognition plans must be simulation-backed")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class CognitionState:
    """Structured operational understanding at one instant."""

    context: str
    active_hypotheses: tuple[Hypothesis, ...]
    verified_explanations: tuple[VerifiedCoreExplanation, ...]
    confidence: float
    timestamp: datetime
    evidence: tuple[Evidence, ...] = ()
    plans: tuple[CognitionPlan, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class OperationalPattern:
    """Verified system knowledge pattern (no user/conversation content)."""

    key: str
    statement: str
    evidence_count: int
    confidence: float

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.statement.strip():
            raise ValueError("pattern key and statement must be non-empty")
        if self.evidence_count < 1:
            raise ValueError("pattern requires evidence_count >= 1")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")
