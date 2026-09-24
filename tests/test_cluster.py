"""Unit tests for AetherOS v1.4 Multi-Device / Cluster Intelligence."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from aetheros.agent import (
    AgentCollector,
    AgentPublisher,
    AgentSnapshot,
    default_demo_peers,
)
from aetheros.cluster import (
    ClusterPanel,
    HeartbeatTracker,
    LocalJSONTransport,
    NodeRegistry,
    aggregate,
    classify_health,
    make_heartbeat_message,
)
from aetheros.cluster.models import ClusterNode
from aetheros.cluster.transport import TransportMessage
from aetheros.policy_engine.models import TelemetrySnapshot


def _node(
    *,
    node_id: str,
    hostname: str,
    cpu: float,
    memory: float = 50.0,
) -> ClusterNode:
    """Build a ClusterNode for aggregator tests."""

    return ClusterNode(
        node_id=node_id,
        hostname=hostname,
        platform="Linux",
        cpu=cpu,
        memory=memory,
        disk=40.0,
        battery=None,
        latency=1.0,
        last_seen=datetime.now(UTC),
    )


def test_transport_json_roundtrip() -> None:
    """LocalJSONTransport should serialize and drain JSON messages."""

    bus = LocalJSONTransport(capacity=50)
    stamp = datetime.now(UTC)
    message = TransportMessage(
        kind="telemetry",
        payload={"node_id": "n1", "cpu": 22.0},
        published_at=stamp,
    )
    bus.publish(message)
    assert bus.pending() == 1
    drained = bus.subscribe()
    assert len(drained) == 1
    assert drained[0].kind == "telemetry"
    assert drained[0].payload["node_id"] == "n1"
    assert bus.pending() == 0


def test_registry_ingest_and_aggregate(tmp_path: Path) -> None:
    """Publisher → registry → aggregate should produce cluster metrics."""

    bus = LocalJSONTransport()
    registry = NodeRegistry(transport=bus, db_path=tmp_path / "cluster.db")
    publisher = AgentPublisher(transport=bus, latency_ms=1.0)
    publisher.publish(
        AgentSnapshot(
            node_id="laptop",
            hostname="Laptop",
            platform="Darwin",
            cpu=22.0,
            memory=40.0,
            disk=30.0,
            battery=80.0,
            collected_at=datetime.now(UTC),
        )
    )
    for peer in default_demo_peers():
        publisher.publish(peer.next_snapshot())
    assert registry.ingest() >= 4
    snap = aggregate(registry)
    assert snap.total_nodes == 4
    assert snap.online_nodes == 4
    assert snap.highest_load_node is not None
    assert snap.highest_load_node.hostname == "Desktop"
    assert snap.average_cpu > 0
    assert any("exceeds cluster average" in a.description for a in snap.alerts)


def test_heartbeat_offline_window() -> None:
    """Nodes outside the online window should classify as offline."""

    tracker = HeartbeatTracker(online_window_seconds=1.0)
    bus_msg = make_heartbeat_message("n1", online=True)
    beat = tracker.heartbeat_from_message(bus_msg)
    assert beat is not None
    tracker.record(beat)
    assert tracker.is_online("n1") is True
    assert tracker.is_online("missing") is False


def test_health_color_rules_only() -> None:
    """Health classification is display-only with expected bands."""

    healthy = _node(node_id="a", hostname="A", cpu=20.0)
    warning = _node(node_id="b", hostname="B", cpu=75.0)
    critical = _node(node_id="c", hostname="C", cpu=95.0)
    assert classify_health(healthy, online=True) == "healthy"
    assert classify_health(warning, online=True) == "warning"
    assert classify_health(critical, online=True) == "critical"
    assert classify_health(healthy, online=False) == "offline"


def test_agent_from_telemetry() -> None:
    """AgentCollector can adapt an existing TelemetrySnapshot."""

    agent = AgentCollector(node_id="local-test", hostname="Laptop")
    snap = TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        cpu_percent=33.0,
        memory_percent=44.0,
        disk_percent=55.0,
        battery_percent=66.0,
        process_count=1,
        top_processes=("python",),
    )
    sample = agent.from_telemetry(snap)
    assert sample.cpu == 33.0
    assert sample.hostname == "Laptop"


def test_sqlite_persistence(tmp_path: Path) -> None:
    """Registry should persist nodes and reload them."""

    db = tmp_path / "cluster.db"
    bus = LocalJSONTransport()
    registry = NodeRegistry(transport=bus, db_path=db)
    registry.upsert(_node(node_id="pi", hostname="Pi", cpu=17.0))
    reloaded = NodeRegistry(transport=LocalJSONTransport(), db_path=db)
    assert reloaded.get("pi") is not None
    assert reloaded.get("pi").hostname == "Pi"


def test_cluster_panel_renders(tmp_path: Path) -> None:
    """Rich cluster panel should include overview fields."""

    bus = LocalJSONTransport()
    registry = NodeRegistry(transport=bus, db_path=tmp_path / "cluster.db")
    registry.upsert(_node(node_id="laptop", hostname="Laptop", cpu=22.0))
    registry.upsert(_node(node_id="desktop", hostname="Desktop", cpu=81.0))
    snap = aggregate(registry)
    online = frozenset(n.node_id for n in snap.nodes)
    panel = ClusterPanel(snapshot=snap, online_ids=online)
    console = Console(record=True, width=100)
    console.print(panel)
    text = console.export_text()
    assert "CLUSTER OVERVIEW" in text
    assert "Desktop" in text
    assert "Laptop" in text
