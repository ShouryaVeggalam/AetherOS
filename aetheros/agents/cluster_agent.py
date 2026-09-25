"""Cluster Agent — compare this host to peer devices.

Responsibility: relative load comparison across the cluster snapshot.
Never remediates remote nodes.
"""

from __future__ import annotations

from aetheros.agents.base import AgentFinding, BaseAgent, DeliberationContext
from aetheros.messaging import AsyncMessageBus


class ClusterAgent(BaseAgent):
    """Compare local pressure to cluster averages when peers exist."""

    def __init__(self, bus: AsyncMessageBus) -> None:
        """Bind to the shared bus."""

        super().__init__(agent_id="cluster", bus=bus)

    def analyze(self, context: DeliberationContext) -> AgentFinding:
        """Emit a comparative finding from optional cluster context."""

        snap = context.snapshot
        cluster = context.cluster
        if cluster is None or cluster.online_nodes <= 1:
            return AgentFinding(
                agent_id=self.agent_id,
                stance="cluster_solo",
                summary="Single-node view — no peer comparison available.",
                confidence=0.75,
                priority=0.1,
                metrics={"local_cpu": snap.cpu_percent, "online_nodes": 1.0},
                evidence=("Cluster snapshot missing or solo.",),
                status="ok",
            )

        delta = snap.cpu_percent - cluster.average_cpu
        evidence = (
            f"Local CPU {snap.cpu_percent:.1f}%",
            f"Cluster avg CPU {cluster.average_cpu:.1f}%",
            f"Online nodes {cluster.online_nodes}/{cluster.total_nodes}",
        )
        if delta >= 20.0:
            stance = "shed_to_peers"
            summary = "Local node hotter than peers — consider shedding load."
            confidence = min(0.9, 0.6 + delta / 100.0)
            priority = 0.75
            status = "warning"
        elif delta <= -20.0:
            stance = "accept_workload"
            summary = "Local node cooler than peers — capacity available."
            confidence = 0.8
            priority = 0.4
            status = "ok"
        else:
            stance = "cluster_balanced"
            summary = "Local load aligned with cluster average."
            confidence = 0.85
            priority = 0.2
            status = "ok"

        return AgentFinding(
            agent_id=self.agent_id,
            stance=stance,
            summary=summary,
            confidence=confidence,
            priority=priority,
            metrics={
                "local_cpu": snap.cpu_percent,
                "cluster_avg_cpu": cluster.average_cpu,
                "online_nodes": float(cluster.online_nodes),
                "cpu_delta": round(delta, 2),
            },
            evidence=evidence,
            status=status,  # type: ignore[arg-type]
        )
