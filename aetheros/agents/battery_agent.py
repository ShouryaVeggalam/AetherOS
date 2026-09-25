"""Battery Agent — estimate energy efficiency trade-offs.

Responsibility: prefer power reduction when on battery or charge is low.
Conflicts with aggressive performance stances are expected and resolved
by the coordinator.
"""

from __future__ import annotations

from aetheros.agents.base import AgentFinding, BaseAgent, DeliberationContext
from aetheros.messaging import AsyncMessageBus


class BatteryAgent(BaseAgent):
    """Recommend efficiency actions based on battery and load."""

    def __init__(self, bus: AsyncMessageBus) -> None:
        """Bind to the shared bus."""

        super().__init__(agent_id="battery", bus=bus)

    def analyze(self, context: DeliberationContext) -> AgentFinding:
        """Estimate whether power should be reduced or held."""

        snap = context.snapshot
        battery = snap.battery_percent
        cpu = snap.cpu_percent
        evidence: list[str] = [f"CPU {cpu:.1f}%"]

        if battery is None:
            return AgentFinding(
                agent_id=self.agent_id,
                stance="hold_power",
                summary="No battery present — efficiency advice idle.",
                confidence=0.9,
                priority=0.1,
                metrics={"cpu_percent": cpu},
                evidence=("Battery unavailable (AC / desktop).",),
                status="ok",
            )

        evidence.append(f"Battery {battery:.0f}%")
        efficiency_bias = context.intent.efficiency_weight / 100.0

        if battery < 25.0 and cpu >= 50.0:
            stance = "reduce_power"
            summary = "Reduce power usage — low battery with elevated load."
            confidence = 0.92
            priority = 0.95
            status = "warning"
        elif battery < 40.0 and cpu >= 70.0:
            stance = "reduce_power"
            summary = "Reduce power usage — mid charge under heavy CPU."
            confidence = 0.85
            priority = 0.8
            status = "warning"
        elif efficiency_bias >= 0.6 and cpu >= 60.0:
            stance = "reduce_power"
            summary = "Reduce power usage — intent favors efficiency."
            confidence = 0.75
            priority = 0.6
            status = "ok"
        else:
            stance = "hold_power"
            summary = "Battery headroom adequate for current load."
            confidence = 0.8
            priority = 0.25
            status = "ok"

        return AgentFinding(
            agent_id=self.agent_id,
            stance=stance,
            summary=summary,
            confidence=confidence,
            priority=priority,
            metrics={
                "battery_percent": float(battery),
                "cpu_percent": cpu,
                "efficiency_weight": float(context.intent.efficiency_weight),
            },
            evidence=tuple(evidence),
            status=status,  # type: ignore[arg-type]
        )
