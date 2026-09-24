"""Aether Agent publisher — push telemetry/heartbeats onto the bus.

JSON only via ClusterTransport. Never opens SSH or runs remote commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from aetheros.agent.collector import AgentSnapshot
from aetheros.cluster.heartbeat import make_heartbeat_message
from aetheros.cluster.transport import ClusterTransport, TransportMessage, utc_now


@dataclass
class AgentPublisher:
    """Publish agent snapshots to a cluster transport.

    Args:
        transport: Local (or future WebSocket) transport.
        latency_ms: Reported transport latency for this agent hop.
    """

    transport: ClusterTransport
    latency_ms: float = 0.5

    def publish(self, snapshot: AgentSnapshot) -> None:
        """Publish one telemetry snapshot (and an accompanying heartbeat)."""

        message = TransportMessage(
            kind="telemetry",
            payload={
                "node_id": snapshot.node_id,
                "hostname": snapshot.hostname,
                "platform": snapshot.platform,
                "cpu": snapshot.cpu,
                "memory": snapshot.memory,
                "disk": snapshot.disk,
                "battery": snapshot.battery,
                "latency": self.latency_ms,
                "last_seen": snapshot.collected_at.isoformat(),
            },
            published_at=utc_now(),
        )
        self.transport.publish(message)
        self.transport.publish(make_heartbeat_message(snapshot.node_id, online=True))


@dataclass
class SyntheticPeer:
    """Demo peer that publishes synthetic telemetry (no remote machine).

    Used so a single-host dashboard can exercise the multi-device view
    without SSH or network agents. Values are local fabrications for UI/tests.
    """

    node_id: str
    hostname: str
    platform: str
    base_cpu: float
    base_memory: float
    base_disk: float
    tick: int = 0

    def next_snapshot(self) -> AgentSnapshot:
        """Advance one synthetic tick and return an AgentSnapshot."""

        self.tick += 1
        wobble = (self.tick % 7) - 3
        cpu = max(1.0, min(99.0, self.base_cpu + wobble * 2.5))
        memory = max(1.0, min(99.0, self.base_memory + (wobble * 0.5)))
        return AgentSnapshot(
            node_id=self.node_id,
            hostname=self.hostname,
            platform=self.platform,
            cpu=cpu,
            memory=memory,
            disk=self.base_disk,
            battery=None,
            collected_at=datetime.now(UTC),
        )


def default_demo_peers() -> tuple[SyntheticPeer, ...]:
    """Example fleet matching the v1.4 dashboard sketch."""

    return (
        SyntheticPeer("demo-desktop", "Desktop", "Linux", 81.0, 64.0, 42.0),
        SyntheticPeer("demo-pi", "Pi", "Linux", 17.0, 35.0, 55.0),
        SyntheticPeer("demo-cloud", "Cloud", "Linux", 34.0, 48.0, 60.0),
    )
