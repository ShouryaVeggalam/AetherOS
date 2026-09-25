"""Unit tests for AetherOS v6 Horizon Planetary Intelligence Network."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from aetheros.edge import EdgeGateway
from aetheros.horizon import (
    DEFAULT_CENSUS,
    FailureScenario,
    GeoPoint,
    HorizonPanel,
    HorizonRuntime,
    LatencyEngine,
    ResilienceSimulator,
    WorldGraph,
    haversine_km,
)
from aetheros.robotics import RobotFleet


def test_haversine_and_latency() -> None:
    """Distance and latency estimates should be finite and explained."""

    na = GeoPoint(40.0, -74.0, "NYC")
    eu = GeoPoint(51.5, -0.1, "LON")
    distance = haversine_km(na, eu)
    assert 5000 < distance < 7000
    est = LatencyEngine().estimate(
        na, eu, network="fiber", source_id="na", target_id="eu"
    )
    assert est.estimated_ms > 0
    assert 0 < est.confidence <= 1
    assert "No live network probe" in est.explanation


def test_world_graph_hierarchy() -> None:
    """World graph should expose Earth → region hierarchy and census."""

    graph = WorldGraph()
    assert graph.node("earth") is not None
    regions = graph.regions()
    assert len(regions) >= 5
    assert graph.census.nodes == DEFAULT_CENSUS.nodes
    assert graph.census.world_health == 99.1
    path = graph.path("earth", regions[0].node_id)
    assert path is not None
    assert path[0] == "earth"


def test_resilience_europe_loss() -> None:
    """Europe −15% capacity simulation should lower world health."""

    graph = WorldGraph()
    report = ResilienceSimulator().europe_capacity_loss(graph, loss_pct=15.0)
    assert report.remaining_capacity_pct == 85.0
    assert report.world_health_after < graph.census.world_health
    assert "Simulation only" in report.explanation
    custom = ResilienceSimulator().simulate(
        graph,
        FailureScenario(
            kind="datacenter_failure",
            target_id="dc.de.1",
            capacity_loss_pct=10.0,
            description="Sample DC failure.",
        ),
    )
    assert custom.cluster_health < 100.0


def test_capacity_horizons() -> None:
    """Capacity plan should cover compute/memory/gpu/storage × 3 horizons."""

    plan = HorizonRuntime().capacity_planner.plan(WorldGraph())
    resources = {f.resource for f in plan.forecasts}
    horizons = {f.horizon for f in plan.forecasts}
    assert resources == {"compute", "memory", "gpu", "storage"}
    assert horizons == {"1h", "24h", "7d"}
    assert all(f.explanation for f in plan.forecasts)


def test_horizon_runtime_and_panel() -> None:
    """HorizonRuntime + panel should render the planetary summary."""

    report = HorizonRuntime().observe(europe_loss_pct=15.0)
    assert report.world_health == 99.1
    assert abs(report.simulated_health - 97.75) < 0.2 or report.simulated_health < 99.1
    assert report.latency
    console = Console(record=True, width=100)
    console.print(HorizonPanel(report=report))
    text = console.export_text()
    assert "HORIZON" in text
    assert "99.1" in text
    assert "Europe" in text or "capacity" in text.lower()


def test_edge_and_robotics_readonly() -> None:
    """Edge and robotics layers should expose inventory without actuation."""

    edge = EdgeGateway().inventory()
    assert edge.sensors
    assert edge.online_ratio >= 0.0
    fleet = RobotFleet().snapshot()
    assert fleet.online_count == len(fleet.robots)
    assert all(a.requires_human_approval for a in fleet.autonomy)


def test_horizon_api_routes(tmp_path: Path) -> None:
    """Horizon FastAPI routes should return JSON without side effects."""

    from fastapi.testclient import TestClient

    from aetheros.api import create_app

    client = TestClient(create_app(memory_db=tmp_path / "cog.db"))
    assert client.get("/world").status_code == 200
    body = client.get("/world").json()
    assert body["regions"] == 42
    assert body["nodes"] == 184_220
    assert client.get("/regions").status_code == 200
    assert client.get("/latency").status_code == 200
    assert client.get("/resilience").json()["remaining_capacity_pct"] == 85.0
    assert client.get("/capacity").status_code == 200
    assert "census" in client.get("/graph").json()
