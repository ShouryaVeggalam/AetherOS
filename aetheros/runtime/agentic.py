"""Agentic runtime — one async deliberation round over the bus.

Wires specialists + coordinator without coupling them. Sync callers use
``deliberate_sync`` which runs a private event loop.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from aetheros.agents.base import AgentFinding, DeliberationContext
from aetheros.agents.battery_agent import BatteryAgent
from aetheros.agents.cluster_agent import ClusterAgent
from aetheros.agents.coordinator import Coordinator, CoordinatorDecision
from aetheros.agents.performance_agent import PerformanceAgent
from aetheros.agents.research_agent import ResearchAgent
from aetheros.agents.security_agent import SecurityAgent
from aetheros.agents.telemetry_agent import TelemetryAgent
from aetheros.cluster.models import ClusterSnapshot
from aetheros.intent.models import IntentProfile
from aetheros.messaging import AsyncMessageBus, make_event
from aetheros.messaging.protocol import BROADCAST
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot


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


@dataclass
class AgenticRuntime:
    """Run a full specialist → coordinator deliberation cycle.

    Attributes:
        bus: Shared async message bus (created if omitted).
    """

    bus: AsyncMessageBus = field(default_factory=AsyncMessageBus)
    _telemetry: TelemetryAgent = field(init=False)
    _performance: PerformanceAgent = field(init=False)
    _battery: BatteryAgent = field(init=False)
    _security: SecurityAgent = field(init=False)
    _cluster: ClusterAgent = field(init=False)
    _research: ResearchAgent = field(init=False)
    _coordinator: Coordinator = field(init=False)
    last_report: AgenticReport | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        """Construct specialist agents on the shared bus."""

        self._telemetry = TelemetryAgent(self.bus)
        self._performance = PerformanceAgent(self.bus)
        self._battery = BatteryAgent(self.bus)
        self._security = SecurityAgent(self.bus)
        self._cluster = ClusterAgent(self.bus)
        self._research = ResearchAgent(self.bus)
        self._coordinator = Coordinator(self.bus)
        # Ensure coordinator receives findings.
        self.bus.subscribe("coordinator")
        for agent_id in (
            "telemetry",
            "performance",
            "battery",
            "security",
            "cluster",
            "research",
        ):
            self.bus.subscribe(agent_id)

    @property
    def specialists(self) -> tuple:
        """Ordered specialist agents (excludes coordinator)."""

        return (
            self._telemetry,
            self._performance,
            self._battery,
            self._security,
            self._cluster,
            self._research,
        )

    @property
    def coordinator(self) -> Coordinator:
        """Return the conflict-resolving coordinator."""

        return self._coordinator

    async def deliberate(
        self,
        snapshot: TelemetrySnapshot,
        intent: IntentProfile,
        *,
        history: tuple[TelemetryPoint, ...] = (),
        cluster: ClusterSnapshot | None = None,
    ) -> AgenticReport:
        """Run one async deliberation round."""

        context = DeliberationContext(
            snapshot=snapshot,
            intent=intent,
            history=history,
            cluster=cluster,
        )
        await self.bus.publish(
            make_event(
                sender="coordinator",
                receiver=BROADCAST,
                type="deliberation.request",
                payload={"intent": intent.name},
            )
        )
        findings: list[AgentFinding] = []
        # Parallel specialist analysis.
        results = await asyncio.gather(
            *(agent.run(context) for agent in self.specialists)
        )
        findings.extend(results)
        decision = await self._coordinator.resolve(
            tuple(findings),
            context=context,
        )
        rows = tuple(
            AgentStatusRow(
                agent_id=agent.agent_id,
                status=agent.status,
                latest_message=agent.last_message,
                confidence=(
                    agent.last_finding.confidence if agent.last_finding else 0.0
                ),
            )
            for agent in (*self.specialists, self._coordinator)
        )
        report = AgenticReport(
            agents=rows,
            findings=tuple(findings),
            decision=decision,
            message_count=len(self.bus.history(limit=500)),
        )
        self.last_report = report
        return report

    def deliberate_sync(
        self,
        snapshot: TelemetrySnapshot,
        intent: IntentProfile,
        *,
        history: tuple[TelemetryPoint, ...] = (),
        cluster: ClusterSnapshot | None = None,
    ) -> AgenticReport:
        """Synchronous wrapper for dashboard / tests."""

        return asyncio.run(
            self.deliberate(
                snapshot,
                intent,
                history=history,
                cluster=cluster,
            )
        )
