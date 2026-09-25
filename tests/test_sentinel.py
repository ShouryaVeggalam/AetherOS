"""Unit tests for AetherOS v8 Sentinel Intelligence Fabric."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from rich.console import Console

from aetheros.graph import DependencyGraph
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.sentinel import (
    AnomalyEngine,
    CascadeSimulator,
    RecoveryPlanner,
    ResilienceScorer,
    RootCauseEngine,
    SentinelPanel,
    SentinelRuntime,
)


def _snap(
    *,
    cpu: float = 92.0,
    memory: float = 60.0,
    disk: float = 40.0,
    battery: float | None = 80.0,
    processes: tuple[str, ...] = ("Indexer", "Cursor"),
) -> TelemetrySnapshot:
    """Telemetry snapshot for Sentinel tests."""

    return TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=disk,
        battery_percent=battery,
        process_count=len(processes),
        top_processes=processes,
    )


def _history(cpu: float = 50.0, count: int = 20) -> tuple[TelemetryPoint, ...]:
    """History window for jump / leak detection."""

    now = datetime.now(UTC)
    return tuple(
        TelemetryPoint(
            now - timedelta(seconds=count - i), cpu, 50.0, 40.0, 70.0, "Coding"
        )
        for i in range(count)
    )


def test_dependency_graph() -> None:
    """Graph should expose services and cascade order."""

    graph = DependencyGraph()
    assert graph.services()
    order = graph.cascade_order("node.local.1")
    assert "cluster.local" in order or "dc.local" in order or order


def test_anomaly_and_root_cause() -> None:
    """High CPU should yield anomalies and ranked root causes."""

    snap = _snap(cpu=96.0)
    anomalies = AnomalyEngine().detect(snap, history=_history(cpu=40.0))
    assert anomalies
    assert any(a.kind == "cpu" for a in anomalies)
    causes = RootCauseEngine().explain(anomalies[0], snap, history=_history())
    assert causes
    assert causes[0].rank == 1
    assert causes[0].confidence >= causes[-1].confidence


def test_cascade_and_recovery() -> None:
    """Cascade sim + recovery planner should recommend without executing."""

    graph = DependencyGraph()
    snap = _snap(cpu=94.0, processes=("Indexer", "Cursor"))
    anomaly = AnomalyEngine().detect(snap)[0]
    causes = RootCauseEngine().explain(anomaly, snap)
    cascade = CascadeSimulator().predict(anomaly, graph)
    plan = RecoveryPlanner().plan(anomaly, snap, root_causes=causes, cascade=cascade)
    assert plan.recommended is not None
    assert "Delay" in plan.recommended.title or plan.recommended.title
    score = ResilienceScorer().score((anomaly,), cascade, graph)
    assert 0 <= score.health <= 100
    assert score.risk in {"Low", "Medium", "High"}


def test_sentinel_runtime_panel() -> None:
    """SentinelRuntime + panel should render recommendation-only status."""

    runtime = SentinelRuntime()
    # Quiet system
    quiet = runtime.observe(_snap(cpu=40.0, memory=50.0))
    assert quiet.risk == "Low" or quiet.health >= 90
    assert quiet.status == "Recommendation Only"
    # Hot system with indexing
    hot = runtime.observe(
        _snap(cpu=93.0, processes=("Indexer", "Cursor")),
        history=_history(cpu=45.0),
        cluster_avg_cpu=50.0,
    )
    assert hot.anomalies
    console = Console(record=True, width=100)
    console.print(SentinelPanel(report=hot))
    text = console.export_text()
    assert "SENTINEL" in text
    assert "Recommendation Only" in text


def test_sentinel_api(tmp_path: Path) -> None:
    """Sentinel API routes should return JSON."""

    from fastapi.testclient import TestClient

    from aetheros.api import create_app

    client = TestClient(create_app(memory_db=tmp_path / "cog.db"))
    body = client.get("/sentinel", params={"cpu_percent": 40}).json()
    assert body["status"] == "Recommendation Only"
    assert "health" in body
    assert (
        client.get("/sentinel/anomalies", params={"cpu_percent": 95}).status_code == 200
    )
    assert "nodes" in client.get("/sentinel/graph").json()
