"""Coordinator — merge agent findings and resolve conflicts.

Produces one explainable recommendation. Never executes actions.
Humans always approve any follow-up.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from aetheros.agents.base import (
    AgentFinding,
    BaseAgent,
    Conflict,
    ConsensusFinding,
    DeliberationContext,
)
from aetheros.agents.bus import BROADCAST, EventBus
from aetheros.agents.events import make_consensus_event
from aetheros.messaging import (
    AsyncMessageBus,
    decision_payload,
    make_event,
)
from aetheros.messaging.protocol import BROADCAST as ASYNC_BROADCAST

# Stances that pull toward performance vs efficiency.
_PERF_STANCES = frozenset(
    {"increase_cpu", "relieve_memory", "relieve_disk", "prefer_performance"}
)
_EFF_STANCES = frozenset({"reduce_power", "prefer_efficiency"})


@dataclass(frozen=True, slots=True)
class CoordinatorDecision:
    """Immutable coordinator output for one deliberation round.

    Attributes:
        recommendation: Human label (e.g. Balanced Mode).
        confidence: Belief in [0, 1].
        reasoning: Explainable conflict / consensus narrative.
        consensus: True when agents largely agree.
        supporting_agents: Agents aligned with the recommendation.
        conflicting_agents: Agents whose stances were overridden.
        findings: All specialist findings considered.
    """

    recommendation: str
    confidence: float
    reasoning: str
    consensus: bool
    supporting_agents: tuple[str, ...]
    conflicting_agents: tuple[str, ...]
    findings: tuple[AgentFinding, ...]

    def __post_init__(self) -> None:
        """Clamp confidence."""

        object.__setattr__(
            self, "confidence", max(0.0, min(1.0, float(self.confidence)))
        )

    def to_consensus_decision(
        self, conflicts: tuple[Conflict, ...] = ()
    ) -> ConsensusDecision:
        """Project to the P4 consensus decision shape (confidence 0–100)."""

        return ConsensusDecision(
            recommendation=self.recommendation,
            supporting_agents=self.supporting_agents,
            conflicting_agents=self.conflicting_agents,
            confidence=round(self.confidence * 100.0, 2),
            reasoning=self.reasoning,
            conflicts=conflicts,
        )


@dataclass(frozen=True, slots=True)
class ConsensusDecision:
    """P4 consensus decision — human-approval recommendation only."""

    recommendation: str
    supporting_agents: tuple[str, ...]
    conflicting_agents: tuple[str, ...]
    confidence: float
    reasoning: str
    conflicts: tuple[Conflict, ...] = ()

    def __post_init__(self) -> None:
        if not self.recommendation.strip():
            raise ValueError("recommendation must be non-empty")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")


class Coordinator(BaseAgent):
    """Resolve multi-agent conflict into one recommendation."""

    def __init__(self, bus: AsyncMessageBus) -> None:
        """Bind to the shared bus."""

        super().__init__(agent_id="coordinator", bus=bus)
        self.last_decision: CoordinatorDecision | None = None

    def analyze(self, context: DeliberationContext) -> AgentFinding:
        """Coordinator does not self-analyze telemetry — use ``resolve``."""

        return AgentFinding(
            agent_id=self.agent_id,
            stance="await_findings",
            summary="Coordinator awaiting specialist findings.",
            confidence=0.0,
            priority=0.0,
            status="idle",
        )

    async def resolve(
        self,
        findings: tuple[AgentFinding, ...],
        *,
        context: DeliberationContext,
    ) -> CoordinatorDecision:
        """Merge findings, detect conflicts, publish decision."""

        self.status = "running"
        decision = self._merge(findings, context)
        self.last_decision = decision
        self.last_finding = AgentFinding(
            agent_id=self.agent_id,
            stance=decision.recommendation.lower().replace(" ", "_"),
            summary=decision.recommendation,
            confidence=decision.confidence,
            priority=1.0,
            evidence=(decision.reasoning,),
            status="ok",
        )
        self.last_message = (
            f"{decision.recommendation} ({decision.confidence:.0%} confidence)"
        )
        self.status = "ok"
        await self.bus.publish(
            make_event(
                sender=self.agent_id,
                receiver=ASYNC_BROADCAST,
                type="coordinator.decision",
                payload=decision_payload(
                    recommendation=decision.recommendation,
                    confidence=decision.confidence,
                    reasoning=decision.reasoning,
                    consensus=decision.consensus,
                    supporting_agents=decision.supporting_agents,
                    conflicting_agents=decision.conflicting_agents,
                ),
            )
        )
        return decision

    def merge_sync(
        self,
        findings: tuple[AgentFinding, ...],
        context: DeliberationContext,
    ) -> CoordinatorDecision:
        """Synchronous merge used by the P4 ConsensusEngine (no bus I/O)."""

        decision = self._merge(findings, context)
        self.last_decision = decision
        return decision

    def _merge(
        self,
        findings: tuple[AgentFinding, ...],
        context: DeliberationContext,
    ) -> CoordinatorDecision:
        """Conflict-aware merge of specialist findings."""

        by_id = {f.agent_id: f for f in findings}
        perf = by_id.get("performance")
        batt = by_id.get("battery")
        research = by_id.get("research")
        security = by_id.get("security")

        perf_push = bool(perf and perf.stance in _PERF_STANCES)
        batt_push = bool(batt and batt.stance in _EFF_STANCES)
        conflicting: list[str] = []
        supporting: list[str] = []

        # Explicit performance vs battery conflict (spec example).
        if perf_push and batt_push and perf is not None and batt is not None:
            perf_gain = perf.priority * perf.confidence
            batt_loss = batt.priority * batt.confidence
            conflicting.extend(["performance", "battery"])
            if batt_loss > perf_gain + 0.05:
                recommendation = "Efficiency Mode"
                reasoning = (
                    "Performance gain is small while battery loss is significant. "
                    f"Battery priority {batt.priority:.0%} outweighs performance "
                    f"urgency {perf.priority:.0%}."
                )
                confidence = min(0.95, 0.55 + batt_loss * 0.4)
                supporting.append("battery")
                if research and research.stance == "prefer_efficiency":
                    supporting.append("research")
                    confidence = min(0.98, confidence + 0.05)
            elif perf_gain > batt_loss + 0.15:
                recommendation = "Performance Mode"
                reasoning = (
                    "Sustained resource pressure outweighs battery cost for now. "
                    f"Performance urgency {perf.priority:.0%} vs battery "
                    f"{batt.priority:.0%}."
                )
                confidence = min(0.95, 0.55 + perf_gain * 0.4)
                supporting.append("performance")
                if research and research.stance == "prefer_performance":
                    supporting.append("research")
            else:
                recommendation = "Balanced Mode"
                reasoning = (
                    "Performance gain is small while battery impact is significant. "
                    "Balanced Mode preserves responsiveness with efficiency guardrails."
                )
                confidence = min(0.95, 0.7 + abs(perf_gain - batt_loss) * 0.2)
                supporting.extend(
                    a for a in ("telemetry", "research", "cluster") if a in by_id
                )
            consensus = False
        else:
            recommendation, confidence, reasoning, supporting, consensus = (
                self._consensus_path(findings, research)
            )
            conflicting = []

        if security and security.stance == "investigate_anomaly":
            reasoning = (
                f"{reasoning} Security notes unusual behavior " f"({security.summary})."
            )
            if "security" not in supporting:
                supporting.append("security")
            confidence = max(0.4, confidence - 0.05)

        if (
            context.intent.efficiency_weight >= 70
            and recommendation == "Performance Mode"
        ):
            recommendation = "Balanced Mode"
            reasoning = (
                f"{reasoning} Intent profile '{context.intent.name}' favors "
                "efficiency, so Performance Mode was softened to Balanced Mode."
            )
            consensus = False

        return CoordinatorDecision(
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning.strip(),
            consensus=consensus,
            supporting_agents=tuple(dict.fromkeys(supporting)),
            conflicting_agents=tuple(dict.fromkeys(conflicting)),
            findings=findings,
        )

    def _consensus_path(
        self,
        findings: tuple[AgentFinding, ...],
        research: AgentFinding | None,
    ) -> tuple[str, float, str, list[str], bool]:
        """Choose a recommendation when no hard conflict exists."""

        if research and research.stance == "prefer_performance":
            return (
                "Performance Mode",
                research.confidence,
                f"Research simulation favors performance. {research.summary}",
                ["research"],
                True,
            )
        if research and research.stance == "prefer_efficiency":
            return (
                "Efficiency Mode",
                research.confidence,
                f"Research simulation favors efficiency. {research.summary}",
                ["research"],
                True,
            )
        if research and research.stance == "prefer_balanced":
            agents = [f.agent_id for f in findings if f.status in ("ok", "warning")]
            return (
                "Balanced Mode",
                max(research.confidence, 0.85),
                f"{len(agents)} agents reached consensus on a balanced posture.",
                agents,
                True,
            )

        perf_votes = sum(1 for f in findings if f.stance in _PERF_STANCES)
        eff_votes = sum(1 for f in findings if f.stance in _EFF_STANCES)
        if perf_votes > eff_votes:
            return (
                "Performance Mode",
                0.7,
                f"{perf_votes} agents lean toward performance relief.",
                [f.agent_id for f in findings if f.stance in _PERF_STANCES],
                True,
            )
        if eff_votes > perf_votes:
            return (
                "Efficiency Mode",
                0.7,
                f"{eff_votes} agents lean toward power reduction.",
                [f.agent_id for f in findings if f.stance in _EFF_STANCES],
                True,
            )
        agents = [f.agent_id for f in findings]
        return (
            "Balanced Mode",
            0.8,
            f"{len(agents)} agents reached consensus.",
            agents,
            True,
        )


def detect_conflicts(findings: tuple[AgentFinding, ...]) -> tuple[Conflict, ...]:
    """Derive explicit Conflict records from opposing specialist stances."""

    by_id = {f.agent_id: f for f in findings}
    conflicts: list[Conflict] = []
    perf = by_id.get("performance")
    batt = by_id.get("battery")
    if perf and batt and perf.stance in _PERF_STANCES and batt.stance in _EFF_STANCES:
        conflicts.append(
            Conflict(
                source="performance",
                target="battery",
                disagreement=(
                    f"Performance wants '{perf.stance}' while battery wants "
                    f"'{batt.stance}'."
                ),
            )
        )
    return tuple(conflicts)


@dataclass
class ConsensusEngine:
    """P4 synchronous multi-agent consensus orchestrator.

    Runs specialists independently, publishes findings on the sync EventBus,
    and merges via the Coordinator. Never executes recommendations.
    """

    bus: EventBus = field(default_factory=EventBus)
    last_decision: ConsensusDecision | None = None
    last_findings: tuple[ConsensusFinding, ...] = ()
    last_conflicts: tuple[Conflict, ...] = ()
    last_raw_findings: tuple[AgentFinding, ...] = ()

    def deliberate(self, context: DeliberationContext) -> ConsensusDecision:
        """Run one evidence-driven consensus round (read-only)."""

        from aetheros.agents.battery_agent import BatteryAgent
        from aetheros.agents.performance_agent import PerformanceAgent
        from aetheros.agents.research_agent import ResearchAgent
        from aetheros.agents.security_agent import SecurityAgent
        from aetheros.agents.telemetry_agent import TelemetryAgent
        from aetheros.messaging import AsyncMessageBus

        shadow = AsyncMessageBus()
        specialists = (
            TelemetryAgent(shadow),
            PerformanceAgent(shadow),
            BatteryAgent(shadow),
            SecurityAgent(shadow),
            ResearchAgent(shadow),
        )
        coordinator = Coordinator(shadow)

        raw: list[AgentFinding] = []
        for agent in specialists:
            finding = agent.analyze(context)
            raw.append(finding)
            self.bus.publish(
                make_consensus_event(
                    sender=finding.agent_id,
                    receiver="coordinator",
                    type="agent.finding",
                    payload={
                        "summary": finding.summary,
                        "stance": finding.stance,
                        "confidence": finding.confidence,
                        "evidence": finding.evidence,
                    },
                    timestamp=datetime.now(UTC),
                )
            )

        decision = coordinator.merge_sync(tuple(raw), context)
        conflicts = detect_conflicts(tuple(raw))
        consensus = decision.to_consensus_decision(conflicts)
        self.bus.publish(
            make_consensus_event(
                sender="coordinator",
                receiver=BROADCAST,
                type="coordinator.decision",
                payload={
                    "recommendation": consensus.recommendation,
                    "confidence": consensus.confidence,
                    "reasoning": consensus.reasoning,
                    "supporting": ",".join(consensus.supporting_agents),
                    "conflicting": ",".join(consensus.conflicting_agents),
                },
                timestamp=datetime.now(UTC),
            )
        )
        self.last_raw_findings = tuple(raw)
        self.last_findings = tuple(f.to_consensus_finding() for f in raw)
        self.last_conflicts = conflicts
        self.last_decision = consensus
        return consensus
