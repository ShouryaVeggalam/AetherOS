"""Unit tests for Context Intelligence Engine (aetheros.context)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta

import pytest
from rich.console import Console

from aetheros.bridge import GraphBridge
from aetheros.context import (
    ContextEngine,
    ContextPanel,
    GraphContext,
    HistoricalPattern,
    IntentContext,
    build_context,
    for_prediction,
    for_reasoning,
    for_simulation,
    match_historical_pattern,
    resolve_intent,
    resolve_operational_intent,
)
from aetheros.graph import ResourceGraph, ResourceNode, build_resource_graph
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.telemetry.models import (
    BatterySnapshot,
    CpuSnapshot,
    DiskSnapshot,
    MemorySnapshot,
    ProcessSnapshot,
    SystemSnapshot,
)


def _stamp() -> datetime:
    return datetime(2026, 1, 1, 9, 0, tzinfo=UTC)


def _tel(**kwargs: float | str | None) -> TelemetrySnapshot:
    return TelemetrySnapshot(
        timestamp=_stamp(),
        cpu_percent=float(kwargs.get("cpu", 40.0)),
        memory_percent=float(kwargs.get("memory", 50.0)),
        disk_percent=float(kwargs.get("disk", 30.0)),
        battery_percent=kwargs.get("battery", 80.0),  # type: ignore[arg-type]
        process_count=2,
        top_processes=("Cursor", "Chrome"),
    )


def _history(n: int = 20, intent: str = "Coding") -> tuple[TelemetryPoint, ...]:
    return tuple(
        TelemetryPoint(
            timestamp=_stamp() + timedelta(minutes=i),
            cpu=38.0 + (i % 5),
            memory=48.0,
            disk=30.0,
            battery=80.0,
            intent=intent,
        )
        for i in range(n)
    )


def _system() -> SystemSnapshot:
    return SystemSnapshot(
        collected_at=_stamp(),
        cpu=CpuSnapshot(40.0, (40.0,), (0.2, 0.2, 0.2)),
        memory=MemorySnapshot(8_000, 4_000, 4_000, 50.0, 0, 0, 0.0),
        disks=(DiskSnapshot("/", 100, 30, 70, 30.0),),
        processes=(ProcessSnapshot(1, "Cursor", "u", 20.0, 10.0, "running"),),
        battery=BatterySnapshot(80.0, True, None),
    )


def test_intent_resolver() -> None:
    """Resolver should prefer evidenced process/manual cues over guessing."""

    from_cursor = resolve_intent(
        manual_profile="Balanced",
        foreground_process="Cursor",
        history=_history(),
    )
    assert from_cursor.name == "CODING"
    assert from_cursor.source in {"foreground", "combined", "history"}
    manual_only = resolve_intent(
        manual_profile="Gaming",
        foreground_process=None,
        history=(),
    )
    assert manual_only.name == "GAMING"
    assert manual_only.source == "manual"
    empty = resolve_intent(manual_profile=None, foreground_process=None, history=())
    assert empty.name == "BALANCED"
    assert empty.confidence <= 20
    low_batt = resolve_intent(
        manual_profile=None,
        foreground_process=None,
        history=(),
        battery_percent=10.0,
    )
    assert low_batt.name == "BATTERY"
    assert resolve_operational_intent(
        manual_profile="AI Training",
        foreground_process="jupyter",
    ).name == "AI"


def test_historical_matcher() -> None:
    """Matcher returns None without enough evidence; scores similar windows."""

    assert match_historical_pattern(
        cpu=40, memory=50, disk=30, intent="CODING", history=()
    ) is None
    pattern = match_historical_pattern(
        cpu=40,
        memory=48,
        disk=30,
        intent="CODING",
        history=_history(25),
    )
    assert pattern is not None
    assert pattern.evidence_count >= 3
    assert 0 <= pattern.similarity <= 100
    assert "Coding" in pattern.label or "Morning" in pattern.label


def test_context_builder() -> None:
    """Builder aggregates graph/bridge/telemetry into GraphContext."""

    system = _system()
    graph = build_resource_graph(system, intent_name="Coding", now=_stamp())
    bridge = GraphBridge(graph)
    tel = TelemetrySnapshot.from_system_snapshot(system)
    ctx = build_context(
        telemetry=tel,
        bridge=bridge,
        history=_history(),
        manual_intent="Coding",
        now=_stamp(),
    )
    assert isinstance(ctx, GraphContext)
    assert ctx.foreground_process == "Cursor"
    assert ctx.active_intent.name == "CODING"
    assert "Charging" in ctx.battery_state or "80" in ctx.battery_state
    assert ctx.simulation_state == "idle"
    assert ctx.cluster_health == "unknown"
    # Without bridge — telemetry top process
    ctx2 = build_context(telemetry=_tel(), history=(), manual_intent=None, now=_stamp())
    assert ctx2.foreground_process == "Cursor"


def test_engine_refresh_and_snapshot_immutability() -> None:
    """Engine refresh stores immutable snapshots; current mirrors snapshot."""

    engine = ContextEngine()
    assert engine.current() is None
    tel = _tel()
    graph = build_resource_graph(_system(), now=_stamp())
    first = engine.refresh(
        tel,
        resource_graph=graph,
        history=_history(),
        manual_intent="Coding",
        now=_stamp(),
    )
    assert engine.snapshot() is first
    assert engine.current() is first
    second = engine.refresh(
        _tel(cpu=55.0),
        resource_graph=graph,
        history=_history(),
        manual_intent="Coding",
        now=_stamp(),
    )
    assert second is not first
    assert first.cpu_load == pytest.approx(40.0)
    assert second.cpu_load == pytest.approx(55.0)
    # Frozen
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        first.cpu_load = 1.0  # type: ignore[misc]


def test_adapters_and_formatter() -> None:
    """Optional adapters and Rich panel should render context."""

    ctx = build_context(
        telemetry=_tel(),
        resource_graph=build_resource_graph(_system(), now=_stamp()),
        history=_history(),
        manual_intent="Coding",
        now=_stamp(),
    )
    pred = for_prediction(ctx)
    assert pred.intent == "CODING"
    reason = for_reasoning(ctx)
    assert reason.foreground_process == "Cursor"
    sim = for_simulation(ctx)
    assert sim.simulation_state == "idle"
    console = Console(record=True, width=90)
    console.print(ContextPanel(context=ctx))
    assert "CONTEXT" in console.export_text()
    console.print(ContextPanel(context=None))
    assert "idle" in console.export_text().lower()


def test_model_validation() -> None:
    """Frozen models reject out-of-range fields."""

    with pytest.raises(ValueError):
        IntentContext("CODING", 120, "manual", 0.0)
    with pytest.raises(ValueError):
        IntentContext("CODING", 50, "manual", -1.0)
    with pytest.raises(ValueError):
        HistoricalPattern("x", 120.0, 1)
    with pytest.raises(ValueError):
        HistoricalPattern("x", 50.0, -1)
    with pytest.raises(ValueError):
        GraphContext(
            timestamp=_stamp(),
            active_intent=IntentContext("CODING", 50, "manual", 0.0),
            foreground_process=None,
            cpu_load=200.0,
            memory_load=10.0,
            disk_load=10.0,
            battery_state="n/a",
            cluster_health="unknown",
            simulation_state="idle",
            historical_pattern=None,
            confidence=50,
        )
    with pytest.raises(ValueError):
        GraphContext(
            timestamp=_stamp(),
            active_intent=IntentContext("CODING", 50, "manual", 0.0),
            foreground_process=None,
            cpu_load=10.0,
            memory_load=10.0,
            disk_load=10.0,
            battery_state="n/a",
            cluster_health="unknown",
            simulation_state="idle",
            historical_pattern=None,
            confidence=200,
        )


def test_history_periods_and_weak_matches() -> None:
    """Cover period labels, intent mismatch penalty, and weak similarity."""

    from aetheros.context.resolver import resolve_historical_match

    evening = tuple(
        TelemetryPoint(
            timestamp=datetime(2026, 1, 1, 19, 0, tzinfo=UTC) + timedelta(minutes=i),
            cpu=90.0,
            memory=90.0,
            disk=90.0,
            battery=50.0,
            intent="Gaming",
        )
        for i in range(10)
    )
    pattern = match_historical_pattern(
        cpu=40,
        memory=40,
        disk=40,
        intent="CODING",
        history=evening,
    )
    # Far resources → likely None or low
    assert pattern is None or pattern.similarity < 60
    night = tuple(
        TelemetryPoint(
            timestamp=datetime(2026, 1, 1, 2, 0, tzinfo=UTC) + timedelta(minutes=i),
            cpu=41.0,
            memory=49.0,
            disk=30.0,
            battery=80.0,
            intent="Coding",
        )
        for i in range(12)
    )
    night_match = resolve_historical_match(
        cpu=40, memory=48, disk=30, intent="CODING", history=night
    )
    assert night_match is not None
    assert "Late-night" in night_match.label or "Coding" in night_match.label
    afternoon = tuple(
        TelemetryPoint(
            timestamp=datetime(2026, 1, 1, 14, 0, tzinfo=UTC) + timedelta(minutes=i),
            cpu=40.0,
            memory=48.0,
            disk=30.0,
            battery=80.0,
            intent="Balanced",
        )
        for i in range(12)
    )
    aft = match_historical_pattern(
        cpu=40, memory=48, disk=30, intent="BALANCED", history=afternoon
    )
    assert aft is not None
    assert "Afternoon" in aft.label or "Balanced" in aft.label


def test_builder_edges_without_battery_and_cluster() -> None:
    """Builder paths for missing battery, simulation nodes, short history."""

    stamp = _stamp()
    tel = TelemetrySnapshot(
        timestamp=stamp,
        cpu_percent=10.0,
        memory_percent=50.0,
        disk_percent=0.0,
        battery_percent=None,
        process_count=0,
        top_processes=(),
    )
    graph = ResourceGraph(
        nodes=(
            ResourceNode("sim:1", "Simulation", "What-if", (), stamp),
            ResourceNode("cluster:1", "Cluster", "Node", (), stamp),
        ),
        edges=(),
    )
    ctx = build_context(
        telemetry=tel,
        resource_graph=graph,
        history=_history(5),
        manual_intent=None,
        now=stamp,
    )
    assert ctx.battery_state == "n/a"
    assert ctx.simulation_state == "active"
    assert ctx.cluster_health == "present"
    # On-battery path
    plugged = SystemSnapshot(
        collected_at=stamp,
        cpu=CpuSnapshot(10.0, (10.0,), (0.1, 0.1, 0.1)),
        memory=MemorySnapshot(1000, 500, 500, 50.0, 0, 0, 0.0),
        disks=(),
        processes=(ProcessSnapshot(1, "Steam", "u", 5.0, 5.0, "running"),),
        battery=BatterySnapshot(40.0, False, None),
    )
    g2 = build_resource_graph(plugged, now=stamp)
    ctx2 = build_context(
        telemetry=TelemetrySnapshot.from_system_snapshot(plugged),
        resource_graph=g2,
        history=(),
        manual_intent="Gaming",
        now=stamp,
    )
    assert "battery" in ctx2.battery_state.lower() or "40" in ctx2.battery_state
    assert resolve_intent(
        manual_profile=None,
        foreground_process="unknown-app",
        history=(),
    ).name == "BALANCED"
