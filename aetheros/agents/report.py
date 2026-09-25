"""Agentic deliberation report types — owned by ``aetheros.agents``.

Kept separate from ``AgenticRuntime`` so presentation (renderer) and
orchestration (runtime) share types without a package cycle.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.agents.base import AgentFinding
from aetheros.agents.coordinator import CoordinatorDecision


@dataclass(frozen=True, slots=True)
class AgentStatusRow:
    """Dashboard row for one agent."""

    agent_id: str
    status: str
    latest_message: str
    confidence: float


@dataclass(frozen=True, slots=True)
class AgenticReport:
    """Immutable multi-agent deliberation report for UI and tests."""

    agents: tuple[AgentStatusRow, ...]
    findings: tuple[AgentFinding, ...]
    decision: CoordinatorDecision
    message_count: int

    @property
    def recommendation(self) -> str:
        """Coordinator recommendation label."""

        return self.decision.recommendation

    @property
    def confidence(self) -> float:
        """Coordinator confidence in [0, 1]."""

        return self.decision.confidence

    @property
    def reasoning(self) -> str:
        """Explainable coordinator reasoning."""

        return self.decision.reasoning
