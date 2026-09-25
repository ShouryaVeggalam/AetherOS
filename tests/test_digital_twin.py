"""Unit tests for Digital Twin 2.0 (host ResourceGraph twin)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from rich.console import Console

from aetheros.graph import build_resource_graph
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.telemetry.models import (
    BatterySnapshot,
    CpuSnapshot,
    DiskSnapshot,
    MemorySnapshot,
    ProcessSnapshot,
    SystemSnapshot,
)
from aetheros.twin import (
    DigitalTwinPanel,
    DigitalTwinSimulator,
    SimulationResult,
    apply_scenario,
    builtin_scenario,
    clone_snapshot,
    create_snapshot,
    diff_twins,
    evaluate,
    format_metric_lines,
    restore_snapshot,
)
from aetheros.twin.simulator import SEED_SCENARIOS, TwinSimulator


def _stamp() -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC)


def _system() -> SystemSnapshot:
    return SystemSnapshot(
        collected_at=_stamp(),
        cpu=CpuSnapshot(41.0, (40.0, 42.0), (0.5, 0.4, 0.3)),
        memory=MemorySnapshot(16_000, 8_000, 8_000, 58.0, 0, 0, 0.0),
        disks=(DiskSnapshot("/", 100, 32, 68, 32.0),),
        processes=(
            ProcessSnapshot(42, "Cursor", "user", 25.0, 12.0, "running"),
            ProcessSnapshot(7, "Chrome", "user", 10.0, 8.0, "running"),
        ),
        battery=BatterySnapshot(80.0, True, None),
    )


def _snap():
    system = _system()
    graph = build_resource_graph(system, intent_name="Coding", now=_stamp())
    tel = TelemetrySnapshot.from_system_snapshot(system)
    return create_snapshot(
        graph, tel, intent="Coding", now=_stamp(), snapshot_id="twin:test"
    )


def test_snapshot_cloning() -> None:
    """create/clone/restore should allocate new graph containers."""

    snap = _snap()
    cloned = clone_snapshot(snap, now=_stamp(), snapshot_id="twin:clone")
    restored = restore_snapshot(snap)
    assert cloned.id != snap.id
    assert cloned.resource_graph is not snap.resource_graph
    assert cloned.resource_graph.node_ids() == snap.resource_graph.node_ids()
    assert restored.resource_graph.node_ids() == snap.resource_graph.node_ids()
    assert snap.intent == "Coding"


def test_scenario_execution() -> None:
    """Scenarios must mutate only the clone's predicted telemetry/graph."""

    snap = _snap()
    cpu_scene = builtin_scenario("CPU_OVERLOAD", now=_stamp())
    simulated = apply_scenario(snap, cpu_scene, now=_stamp())
    assert simulated.telemetry.cpu_percent > snap.telemetry.cpu_percent
    assert snap.telemetry.cpu_percent == pytest.approx(41.0)
    mem = apply_scenario(
        snap, builtin_scenario("MEMORY_PRESSURE", now=_stamp()), now=_stamp()
    )
    assert mem.telemetry.memory_percent > snap.telemetry.memory_percent
    batt = apply_scenario(
        snap, builtin_scenario("BATTERY_LOW", now=_stamp()), now=_stamp()
    )
    assert batt.telemetry.battery_percent == pytest.approx(10.0)
    disk = apply_scenario(
        snap, builtin_scenario("DISK_SATURATION", now=_stamp()), now=_stamp()
    )
    assert disk.telemetry.disk_percent > snap.telemetry.disk_percent
    offline = apply_scenario(
        snap, builtin_scenario("NODE_OFFLINE", now=_stamp()), now=_stamp()
    )
    assert offline.telemetry.process_count == snap.telemetry.process_count - 1
    custom = builtin_scenario(
        "CUSTOM",
        now=_stamp(),
        custom_mods=(("cpu_delta", "10"), ("memory_delta", "5")),
    )
    custom_sim = apply_scenario(snap, custom, now=_stamp())
    assert custom_sim.telemetry.cpu_percent > snap.telemetry.cpu_percent
    with pytest.raises(ValueError):
        builtin_scenario("NOPE")
    with pytest.raises(ValueError):
        builtin_scenario("CUSTOM", custom_mods=())


def test_evaluator_and_simulator_pipeline() -> None:
    """DigitalTwinSimulator should return result + diff without touching baseline."""

    snap = _snap()
    scene = builtin_scenario("CPU_OVERLOAD", now=_stamp())
    report = DigitalTwinSimulator().run(snap, scene, now=_stamp())
    assert report.result.predicted_cpu > snap.telemetry.cpu_percent
    assert 0 <= report.result.stability <= 100
    assert 0 <= report.result.confidence <= 100
    assert report.result.risk in {"low", "medium", "high", "critical"}
    assert report.result.reasoning
    assert report.diff.changed_metrics
    # Baseline identity preserved in report clone chain
    assert report.baseline.telemetry.cpu_percent == pytest.approx(41.0)
    # Direct evaluate API
    simulated = apply_scenario(snap, scene, now=_stamp())
    result = evaluate(snap, simulated, scene)
    assert isinstance(result, SimulationResult)


def test_diff_engine() -> None:
    """Diff should report metric and topology changes."""

    snap = _snap()
    simulated = apply_scenario(
        snap, builtin_scenario("NODE_OFFLINE", now=_stamp()), now=_stamp()
    )
    diff = diff_twins(snap, simulated)
    assert diff.removed_nodes
    lines = format_metric_lines(diff)
    assert isinstance(lines, tuple)
    cpu_sim = apply_scenario(
        snap, builtin_scenario("CPU_OVERLOAD", now=_stamp()), now=_stamp()
    )
    cpu_diff = diff_twins(snap, cpu_sim)
    assert any(m.metric == "cpu" for m in cpu_diff.changed_metrics)
    assert any("CPU" in line for line in format_metric_lines(cpu_diff))


def test_formatter_and_global_twin_compat() -> None:
    """Panel renders twin report; global TwinSimulator remains intact."""

    snap = _snap()
    report = DigitalTwinSimulator().run(
        snap, builtin_scenario("CPU_OVERLOAD", now=_stamp()), now=_stamp()
    )
    console = Console(record=True, width=100)
    console.print(DigitalTwinPanel(report=report))
    text = console.export_text()
    assert "DIGITAL TWIN" in text
    assert "Simulation Only" in text
    console.print(
        DigitalTwinPanel(
            report=None,
            scenario=builtin_scenario("CPU_OVERLOAD", now=_stamp()),
            baseline=snap,
        )
    )
    assert "idle" in console.export_text().lower() or "V" in console.export_text()
    # Global twin regression
    outcome = TwinSimulator().simulate(SEED_SCENARIOS[0])
    assert outcome.capacity >= 0


def test_simulation_result_bounds() -> None:
    """SimulationResult should reject out-of-range scores."""

    scene = builtin_scenario("CPU_OVERLOAD", now=_stamp())
    with pytest.raises(ValueError):
        SimulationResult(
            predicted_cpu=120,
            predicted_memory=10,
            predicted_disk=10,
            predicted_battery=None,
            stability=50,
            confidence=50,
            reasoning="x",
            risk="low",
            bottleneck="cpu",
            scenario=scene,
        )
