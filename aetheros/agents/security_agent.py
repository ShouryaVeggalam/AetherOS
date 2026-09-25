"""Security Agent — detect unusual resource behavior.

Responsibility: flag anomalous process/resource patterns (read-only).
Does not quarantine, kill, or modify processes.
"""

from __future__ import annotations

from aetheros.agents.base import AgentFinding, BaseAgent, DeliberationContext
from aetheros.messaging import AsyncMessageBus

# Public, well-known interactive / tooling names — not a blocklist.
_KNOWN_BENIGN = frozenset(
    {
        "cursor",
        "chrome",
        "code",
        "python",
        "node",
        "firefox",
        "safari",
        "terminal",
        "zsh",
        "bash",
        "dock",
        "finder",
        "windowserver",
    }
)


class SecurityAgent(BaseAgent):
    """Surface unusual utilization patterns for human review."""

    def __init__(self, bus: AsyncMessageBus) -> None:
        """Bind to the shared bus."""

        super().__init__(agent_id="security", bus=bus)

    def analyze(self, context: DeliberationContext) -> AgentFinding:
        """Compare current load and process mix to recent history."""

        snap = context.snapshot
        history = context.history
        evidence: list[str] = []

        avg_cpu = (
            sum(p.cpu for p in history) / len(history) if history else snap.cpu_percent
        )
        spike = snap.cpu_percent - avg_cpu
        evidence.append(
            f"CPU now {snap.cpu_percent:.1f}% vs history avg {avg_cpu:.1f}%"
        )

        unknown = tuple(
            name for name in snap.top_processes[:5] if name.lower() not in _KNOWN_BENIGN
        )
        if unknown:
            evidence.append(f"Less-familiar top process: {unknown[0]}")

        if spike >= 35.0 and snap.cpu_percent >= 85.0:
            stance = "investigate_anomaly"
            summary = "Unusual resource spike — investigate elevated CPU."
            confidence = min(0.9, 0.55 + spike / 100.0)
            priority = 0.85
            status = "warning"
        elif unknown and snap.cpu_percent >= 80.0:
            stance = "investigate_anomaly"
            summary = "High CPU from less-familiar process — review recommended."
            confidence = 0.7
            priority = 0.7
            status = "warning"
        else:
            stance = "security_nominal"
            summary = "No unusual resource behavior detected."
            confidence = 0.8
            priority = 0.15
            status = "ok"

        return AgentFinding(
            agent_id=self.agent_id,
            stance=stance,
            summary=summary,
            confidence=confidence,
            priority=priority,
            metrics={
                "cpu_percent": snap.cpu_percent,
                "cpu_spike": round(spike, 2),
                "unknown_top": float(len(unknown)),
            },
            evidence=tuple(evidence),
            status=status,  # type: ignore[arg-type]
        )
