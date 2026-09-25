"""Base agent contract for the agentic intelligence layer.

Each agent owns one specialty, produces an immutable finding, and
publishes it on the bus. Agents never call peers directly and never
execute OS actions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

from aetheros.cluster.models import ClusterSnapshot
from aetheros.intent.models import IntentProfile
from aetheros.messaging import AsyncMessageBus, finding_payload, make_event
from aetheros.messaging.protocol import BROADCAST, AgentId
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot

AgentStatus = Literal["idle", "running", "ok", "warning", "error"]


@dataclass(frozen=True, slots=True)
class AgentFinding:
    """Immutable specialist output from one agent.

    Attributes:
        agent_id: Producing agent.
        stance: Machine-oriented recommendation stance.
        summary: Short human summary.
        confidence: Belief in [0, 1].
        priority: Urgency in [0, 1].
        metrics: Supporting numeric values.
        evidence: Public systems evidence strings.
        status: Agent health after analysis.
    """

    agent_id: str
    stance: str
    summary: str
    confidence: float
    priority: float
    metrics: dict[str, float] = field(default_factory=dict)
    evidence: tuple[str, ...] = ()
    status: AgentStatus = "ok"

    def __post_init__(self) -> None:
        """Clamp confidence and priority."""

        object.__setattr__(
            self, "confidence", max(0.0, min(1.0, float(self.confidence)))
        )
        object.__setattr__(self, "priority", max(0.0, min(1.0, float(self.priority))))


@dataclass(frozen=True, slots=True)
class DeliberationContext:
    """Read-only inputs shared by all agents for one deliberation round."""

    snapshot: TelemetrySnapshot
    intent: IntentProfile
    history: tuple[TelemetryPoint, ...] = ()
    cluster: ClusterSnapshot | None = None


@dataclass
class BaseAgent(ABC):
    """Abstract specialist agent.

    Attributes:
        agent_id: Stable protocol id.
        bus: Shared async message bus.
        status: Latest lifecycle status for the dashboard.
        last_finding: Most recent finding, if any.
        last_message: Latest published summary line.
    """

    agent_id: AgentId
    bus: AsyncMessageBus
    status: AgentStatus = "idle"
    last_finding: AgentFinding | None = None
    last_message: str = ""

    @abstractmethod
    def analyze(self, context: DeliberationContext) -> AgentFinding:
        """Produce a finding from read-only context (pure analysis)."""

    async def run(self, context: DeliberationContext) -> AgentFinding:
        """Analyze, publish finding on the bus, and update status."""

        self.status = "running"
        try:
            finding = self.analyze(context)
            self.last_finding = finding
            self.last_message = finding.summary
            self.status = finding.status
            await self._publish_finding(finding)
            return finding
        except Exception as exc:  # pragma: no cover - defensive
            self.status = "error"
            self.last_message = f"error: {exc}"
            raise

    async def _publish_finding(self, finding: AgentFinding) -> None:
        """Emit ``agent.finding`` to the coordinator (and broadcast)."""

        payload: dict[str, Any] = finding_payload(
            stance=finding.stance,
            summary=finding.summary,
            confidence=finding.confidence,
            priority=finding.priority,
            metrics=finding.metrics,
            evidence=finding.evidence,
        )
        event = make_event(
            sender=self.agent_id,
            receiver="coordinator",
            type="agent.finding",
            payload=payload,
        )
        await self.bus.publish(event)
        status_event = make_event(
            sender=self.agent_id,
            receiver=BROADCAST,
            type="agent.status",
            payload={"status": finding.status, "summary": finding.summary},
        )
        await self.bus.publish(status_event)
