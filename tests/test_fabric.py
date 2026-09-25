"""Unit tests for AetherOS v9 Aether Fabric."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from aetheros.fabric import (
    DEFAULT_UNIVERSE,
    FabricGraph,
    FabricPanel,
    FabricRuntime,
    Federation,
    Synchronizer,
)
from aetheros.genesis.knowledge_base import KnowledgeBase
from aetheros.protocol import dumps_event, loads_event, make_event
from aetheros.twin import GlobalTwin, TwinSimulator


def test_protocol_roundtrip() -> None:
    """Events should serialize and deserialize with version stamps."""

    event = make_event(
        kind="telemetry.snapshot",
        sender_id="node.local.pc",
        payload={"cpu": 40.0, "health": 98.0},
    )
    raw = dumps_event(event)
    restored = loads_event(raw)
    assert restored.sender_id == event.sender_id
    assert restored.payload["cpu"] == 40.0


def test_federation_and_sync() -> None:
    """Federation publishes snapshots; synchronizer merges eventually."""

    fed = Federation()
    assert fed.health().member_count >= 4
    sync = Synchronizer(federation=fed)
    # Drain may be empty if observer mailbox already received publishes at init.
    report = sync.tick(observer_id="node.local.pc")
    assert report.synchronization >= 0.0
    assert sync.view()


def test_fabric_graph_and_twin() -> None:
    """Universal graph and global twin should produce simulation outcomes."""

    graph = FabricGraph()
    assert any(n.kind == "gpu" for n in graph.nodes())
    assert any(e.relation == "SYNCHRONIZES" for e in graph.edges())
    twin = GlobalTwin().observe()
    assert twin.plan.outcomes
    assert twin.status == "Simulation Only"
    outcome = TwinSimulator().simulate(twin.plan.outcomes[0].scenario)
    assert 0 <= outcome.risk <= 100


def test_fabric_runtime_panel(tmp_path: Path) -> None:
    """FabricRuntime + panel should render census example figures."""

    runtime = FabricRuntime(knowledge=KnowledgeBase(tmp_path / "kb.db"))
    report = runtime.observe()
    assert report.connected_nodes == DEFAULT_UNIVERSE.connected_nodes
    assert report.synchronization == 99.98
    assert report.global_health == 98.7
    assert "Human Controlled" in report.status
    console = Console(record=True, width=100)
    console.print(FabricPanel(report=report))
    text = console.export_text()
    assert "FABRIC" in text
    assert "241,880" in text or "241880" in text


def test_fabric_api(tmp_path: Path) -> None:
    """Fabric API routes should return read-only JSON."""

    from fastapi.testclient import TestClient

    from aetheros.api import create_app

    client = TestClient(create_app(memory_db=tmp_path / "cog.db"))
    health = client.get("/health").json()
    assert health["status"] == "ok"
    assert health["control"] == "human"
    fabric = client.get("/fabric").json()
    assert fabric["connected_nodes"] == 241_880
    assert fabric["regions"] == 47
    assert client.get("/federation").status_code == 200
    assert client.get("/twin").status_code == 200
    assert "nodes" in client.get("/fabric/graph").json()
    assert "records" in client.get("/knowledge").json()
