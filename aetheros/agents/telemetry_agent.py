"""Telemetry Agent — collects and summarizes live metrics.

Responsibility: normalize the current sample into an agent finding.
Does not recommend interventions; other agents consume the metrics.
"""

from __future__ import annotations

from aetheros.agents.base import AgentFinding, BaseAgent, DeliberationContext
from aetheros.messaging import AsyncMessageBus


class TelemetryAgent(BaseAgent):
    """Summarize the active telemetry snapshot for peer agents."""

    def __init__(self, bus: AsyncMessageBus) -> None:
        """Bind to the shared bus."""

        super().__init__(agent_id="telemetry", bus=bus)

    def analyze(self, context: DeliberationContext) -> AgentFinding:
        """Emit a metrics digest with collection confidence."""

        snap = context.snapshot
        evidence = (
            f"CPU {snap.cpu_percent:.1f}%",
            f"Memory {snap.memory_percent:.1f}%",
            f"Disk {snap.disk_percent:.1f}%",
            f"Processes sampled: {snap.process_count}",
        )
        if snap.battery_percent is not None:
            evidence = (*evidence, f"Battery {snap.battery_percent:.0f}%")
        pressure = max(snap.cpu_percent, snap.memory_percent, snap.disk_percent) / 100.0
        return AgentFinding(
            agent_id=self.agent_id,
            stance="report_metrics",
            summary=(
                f"Collected metrics — CPU {snap.cpu_percent:.0f}% / "
                f"RAM {snap.memory_percent:.0f}% / Disk {snap.disk_percent:.0f}%."
            ),
            confidence=0.95,
            priority=min(1.0, pressure),
            metrics={
                "cpu_percent": snap.cpu_percent,
                "memory_percent": snap.memory_percent,
                "disk_percent": snap.disk_percent,
                "process_count": float(snap.process_count),
            },
            evidence=evidence,
            status="ok",
        )
