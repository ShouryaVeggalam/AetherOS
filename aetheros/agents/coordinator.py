"""Coordinator — merge agent findings and resolve conflicts.

Produces one explainable recommendation. Never executes actions.
Humans always approve any follow-up.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.agents.base import AgentFinding, BaseAgent, DeliberationContext
from aetheros.messaging import (
    AsyncMessageBus,
    decision_payload,
    make_event,
)
from aetheros.messaging.protocol import BROADCAST

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
                receiver=BROADCAST,
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
                    "Performance gain is small while battery loss is significant "
                    "enough to avoid a pure performance bias. "
                    "Balanced Mode preserves responsiveness with efficiency guardrails."
                )
                confidence = min(0.95, 0.7 + abs(perf_gain - batt_loss) * 0.2)
                supporting.extend(
                    a for a in ("telemetry", "research", "cluster") if a in by_id
                )
            consensus = False
        else:
            # Soft consensus path — lean on research + majority stance family.
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

        # Intent soft bias.
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
