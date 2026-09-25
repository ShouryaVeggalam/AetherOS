"""Performance Agent — analyze CPU, RAM, and disk pressure.

Responsibility: detect resource contention and recommend performance-
oriented stances. Never executes allocation changes.
"""

from __future__ import annotations

from aetheros.agents.base import AgentFinding, BaseAgent, DeliberationContext
from aetheros.messaging import AsyncMessageBus


class PerformanceAgent(BaseAgent):
    """Recommend performance relief when resources are contended."""

    def __init__(self, bus: AsyncMessageBus) -> None:
        """Bind to the shared bus."""

        super().__init__(agent_id="performance", bus=bus)

    def analyze(self, context: DeliberationContext) -> AgentFinding:
        """Score CPU/RAM/disk and choose a performance stance."""

        snap = context.snapshot
        cpu = snap.cpu_percent
        mem = snap.memory_percent
        disk = snap.disk_percent
        evidence: list[str] = [
            f"CPU load {cpu:.1f}%",
            f"Memory load {mem:.1f}%",
            f"Disk load {disk:.1f}%",
        ]
        if snap.top_processes:
            evidence.append(f"Top process: {snap.top_processes[0]}")

        if cpu >= 90.0:
            stance = "increase_cpu"
            summary = "Increase CPU allocation — sustained high utilization."
            confidence = min(0.98, 0.7 + (cpu - 90.0) / 50.0)
            priority = 0.9
            status = "warning"
        elif mem >= 90.0:
            stance = "relieve_memory"
            summary = "Relieve memory pressure — RAM near capacity."
            confidence = min(0.95, 0.65 + (mem - 90.0) / 40.0)
            priority = 0.85
            status = "warning"
        elif disk >= 90.0:
            stance = "relieve_disk"
            summary = "Reduce disk contention — volume nearly full."
            confidence = 0.8
            priority = 0.7
            status = "warning"
        elif cpu >= 70.0:
            stance = "increase_cpu"
            summary = "Modest CPU headroom needed for responsiveness."
            confidence = 0.65
            priority = 0.55
            status = "ok"
        else:
            stance = "hold_performance"
            summary = "Performance within acceptable bounds."
            confidence = 0.85
            priority = 0.2
            status = "ok"

        return AgentFinding(
            agent_id=self.agent_id,
            stance=stance,
            summary=summary,
            confidence=confidence,
            priority=priority,
            metrics={"cpu_percent": cpu, "memory_percent": mem, "disk_percent": disk},
            evidence=tuple(evidence),
            status=status,  # type: ignore[arg-type]
        )
