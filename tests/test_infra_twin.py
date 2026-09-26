"""Tests for AetherOS v6.0 P2 Infrastructure Digital Twin (simulation only)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from rich.console import Console

from aetheros.cloud import seed_demo_cloud
from aetheros.infra_twin import (
    InfrastructureDiff,
    InfrastructureSnapshot,
    InfrastructureTwinPanel,
    InfrastructureTwinSimulator,
    SimulationResult,
    TopologyNode,
    TwinScenario,
    apply_scenario,
    availability_pct,
    clone_snapshot,
    content_fingerprint,
    demo_snapshot,
    diff_snapshots,
    evaluate,
    from_cloud_snapshot,
    library,
    mean_latency,
    mean_load,
    risk_level,
)


def test_topology_node_validation_and_roundtrip() -> None:
    node = TopologyNode(
        id="n1",
        kind="node",
        region="us-east-1",
        provider="aws",
        load=10.0,
        latency_ms=4.0,
    )
    assert TopologyNode.from_dict(node.to_dict()).id == "n1"
    with pytest.raises(ValueError):
        TopologyNode(id="", kind="node", region="r", provider="aws")
    with pytest.raises(ValueError):
        TopologyNode(id="n", kind="", region="r", provider="aws")
    with pytest.raises(ValueError):
        TopologyNode(id="n", kind="node", region="", provider="aws")
    with pytest.raises(ValueError):
        TopologyNode(id="n", kind="node", region="r", provider="aws", load=120.0)
    with pytest.raises(ValueError):
        TopologyNode(id="n", kind="node", region="r", provider="aws", latency_ms=-1.0)
    with pytest.raises(ValueError):
        TopologyNode.from_dict(
            {
                "id": "n",
                "kind": "node",
                "region": "r",
                "provider": "aws",
                "metadata": "bad",
            }
        )


def test_snapshot_clone_is_independent() -> None:
    snap = demo_snapshot(timestamp=datetime(2026, 9, 26, tzinfo=UTC))
    cloned = clone_snapshot(snap, new_id="clone-test")
    assert cloned.id == "clone-test"
    assert cloned.node_count == snap.node_count
    assert cloned is not snap
    assert cloned.topology[0] is not snap.topology[0]
    assert cloned.topology[0].metadata is not snap.topology[0].metadata
    # Mutating clone metadata dict must not affect original (frozen copies).
    assert snap.topology[0].id == cloned.topology[0].id
    fp1 = content_fingerprint(snap)
    fp2 = content_fingerprint(cloned)
    assert fp1 == fp2


def test_snapshot_roundtrip_and_validation() -> None:
    snap = demo_snapshot()
    restored = InfrastructureSnapshot.from_dict(snap.to_dict())
    assert restored.regions == snap.regions
    with pytest.raises(ValueError):
        InfrastructureSnapshot.from_dict(
            {
                "id": "x",
                "timestamp": "2026-09-26T00:00:00+00:00",
                "topology": "bad",
                "resources": [],
                "regions": [],
            }
        )
    with pytest.raises(ValueError):
        InfrastructureSnapshot(
            id="",
            timestamp=datetime.now(UTC),
            topology=(),
            resources=(),
            regions=(),
        )


def test_from_cloud_snapshot() -> None:
    cloud = seed_demo_cloud().last_snapshot
    assert cloud is not None
    twin = from_cloud_snapshot(cloud)
    assert twin.node_count == cloud.resource_count
    assert twin.regions


def test_scenario_library_and_kinds() -> None:
    scenarios = library()
    assert len(scenarios) == 7
    kinds = {s.kind for s in scenarios}
    assert "REGION_OUTAGE" in kinds
    assert "WORKLOAD_SURGE" in kinds
    with pytest.raises(ValueError):
        TwinScenario(id="x", name="NOT_A_KIND", description="nope", variables={})


def test_apply_each_scenario() -> None:
    baseline = demo_snapshot()
    original_available = baseline.available_nodes
    for scenario in library():
        cloned = clone_snapshot(baseline)
        after = apply_scenario(cloned, scenario)
        assert after.id == cloned.id
        # Baseline untouched.
        assert baseline.available_nodes == original_available
        assert baseline.topology[0].available is True


def test_region_outage_marks_region_unavailable() -> None:
    baseline = demo_snapshot()
    scenario = TwinScenario(
        id="t",
        name="REGION_OUTAGE",
        description="outage",
        variables={"kind": "REGION_OUTAGE", "region": "us-east-1"},
    )
    after = apply_scenario(clone_snapshot(baseline), scenario)
    east = [n for n in after.topology if n.region == "us-east-1"]
    assert east
    assert all(not n.available for n in east)
    west = [n for n in after.topology if n.region == "us-west-2"]
    assert all(n.available for n in west)


def test_node_failure_and_latency_and_gpu() -> None:
    baseline = demo_snapshot()
    fail = apply_scenario(
        clone_snapshot(baseline),
        TwinScenario(
            id="f",
            name="NODE_FAILURE",
            description="f",
            variables={"kind": "NODE_FAILURE", "count": 2},
        ),
    )
    assert fail.available_nodes == baseline.available_nodes - 2

    lat = apply_scenario(
        clone_snapshot(baseline),
        TwinScenario(
            id="l",
            name="NETWORK_LATENCY",
            description="l",
            variables={"kind": "NETWORK_LATENCY", "latency_delta_ms": 14.0},
        ),
    )
    assert mean_latency(lat) > mean_latency(baseline)

    gpu = apply_scenario(
        clone_snapshot(baseline),
        TwinScenario(
            id="g",
            name="GPU_EXPANSION",
            description="g",
            variables={"kind": "GPU_EXPANSION", "capacity_factor": 2.0},
        ),
    )
    assert gpu.topology[0].capacity == baseline.topology[0].capacity * 2.0
    assert gpu.topology[0].load < baseline.topology[0].load


def test_workload_surge_disk_custom() -> None:
    baseline = demo_snapshot()
    surge = apply_scenario(
        clone_snapshot(baseline),
        TwinScenario(
            id="s",
            name="WORKLOAD_SURGE",
            description="s",
            variables={"kind": "WORKLOAD_SURGE", "workloads": 500},
        ),
    )
    assert mean_load(surge) > mean_load(baseline)

    disk = apply_scenario(
        clone_snapshot(baseline),
        TwinScenario(
            id="d",
            name="DISK_FAILURE",
            description="d",
            variables={"kind": "DISK_FAILURE", "fraction": 0.25},
        ),
    )
    assert disk.available_nodes < baseline.available_nodes

    custom = apply_scenario(
        clone_snapshot(baseline),
        TwinScenario(
            id="c",
            name="CUSTOM",
            description="c",
            variables={"kind": "CUSTOM", "load_delta": 5.0, "latency_delta_ms": 1.0},
        ),
    )
    assert mean_load(custom) > mean_load(baseline)


def test_evaluator_and_risk_levels() -> None:
    snap = demo_snapshot()
    scenario = library()[0]
    result = evaluate(snap, scenario, baseline=snap)
    assert isinstance(result, SimulationResult)
    assert 0 <= result.availability <= 100
    assert result.confidence >= 40
    assert risk_level(99.0, 4.0, 40.0) == "low"
    assert risk_level(90.0, 20.0, 75.0) == "medium"
    assert risk_level(80.0, 50.0, 90.0) == "high"
    assert risk_level(40.0, 10.0, 99.0) == "critical"
    empty = InfrastructureSnapshot(
        id="empty",
        timestamp=datetime.now(UTC),
        topology=(),
        resources=(),
        regions=(),
    )
    assert availability_pct(empty) == 0.0
    assert mean_load(empty) == 100.0
    assert mean_latency(empty) == 999.0


def test_diff_engine() -> None:
    baseline = demo_snapshot()
    after = apply_scenario(clone_snapshot(baseline), library()[0])
    delta = diff_snapshots(baseline, after)
    assert isinstance(delta, InfrastructureDiff)
    assert delta.nodes_after <= delta.nodes_before
    assert delta.availability_after <= delta.availability_before
    assert delta.degraded
    assert delta.to_dict()["nodes_before"] == delta.nodes_before


def test_simulator_pipeline() -> None:
    sim = InfrastructureTwinSimulator()
    run = sim.simulate_kind("REGION_OUTAGE")
    assert run.result.scenario_id
    assert run.diff.availability_before >= run.diff.availability_after
    # Baseline object identity preserved on simulator.
    assert run.baseline is sim.baseline
    assert run.cloned.id != run.baseline.id
    again = sim.simulate(library()[1])
    assert again.scenario.kind == "NODE_FAILURE"
    with pytest.raises(ValueError):
        sim.simulate_kind("NOPE")


def test_simulation_result_validation() -> None:
    with pytest.raises(ValueError):
        SimulationResult(
            cpu=120,
            memory=10,
            latency=1,
            availability=99,
            stability=90,
            confidence=90,
        )
    with pytest.raises(ValueError):
        SimulationResult(
            cpu=10,
            memory=10,
            latency=-1,
            availability=99,
            stability=90,
            confidence=90,
        )


def test_formatter_views() -> None:
    sim = InfrastructureTwinSimulator()
    run = sim.simulate_kind("NETWORK_LATENCY")
    console = Console(record=True, width=100)
    for view in ("snapshot", "library", "simulation", "diff", "availability"):
        panel = InfrastructureTwinPanel(
            snapshot=sim.baseline,
            scenarios=sim.scenarios(),
            run=run,
            view=view,
        )
        console.print(panel)
        text = console.export_text()
        assert "Simulation Only" in text
    idle = InfrastructureTwinPanel()
    console.print(idle)
    assert (
        "idle" in console.export_text().lower()
        or "Simulation Only" in console.export_text()
    )
    # empty simulation view
    panel = InfrastructureTwinPanel(snapshot=sim.baseline, view="simulation")
    console.print(panel)


def test_twin_scenario_roundtrip() -> None:
    scenario = library()[0]
    assert TwinScenario.from_dict(scenario.to_dict()).id == scenario.id


def test_clone_naive_timestamp_and_set_baseline() -> None:
    snap = demo_snapshot(timestamp=datetime(2026, 1, 1, 0, 0, 0))
    cloned = clone_snapshot(snap, timestamp=datetime(2026, 2, 1, 0, 0, 0))
    assert cloned.timestamp.tzinfo is not None
    sim = InfrastructureTwinSimulator(baseline=snap)
    other = demo_snapshot()
    sim.set_baseline(other)
    assert sim.baseline is other


def test_scenario_default_region_and_bad_kind() -> None:
    snap = demo_snapshot()
    # empty region variable → first region
    after = apply_scenario(
        clone_snapshot(snap),
        TwinScenario(
            id="r",
            name="REGION_OUTAGE",
            description="r",
            variables={"kind": "REGION_OUTAGE", "region": ""},
        ),
    )
    assert after.available_nodes < snap.available_nodes
    with pytest.raises(ValueError):
        apply_scenario(
            clone_snapshot(snap),
            TwinScenario(
                id="bad",
                name="CUSTOM",
                description="x",
                variables={"kind": "NOT_REAL"},
            ),
        )


def test_model_extra_validation() -> None:
    with pytest.raises(ValueError):
        TopologyNode(id="n", kind="node", region="r", provider="aws", capacity=5000.0)
    with pytest.raises(ValueError):
        InfrastructureSnapshot.from_dict(
            {
                "id": "x",
                "timestamp": "2026-09-26T00:00:00+00:00",
                "topology": [],
                "resources": "bad",
                "regions": [],
            }
        )
    with pytest.raises(ValueError):
        InfrastructureSnapshot.from_dict(
            {
                "id": "x",
                "timestamp": "2026-09-26T00:00:00+00:00",
                "topology": [],
                "resources": [],
                "regions": "bad",
            }
        )
    with pytest.raises(ValueError):
        TwinScenario(
            id="", name="CUSTOM", description="d", variables={"kind": "CUSTOM"}
        )
    with pytest.raises(ValueError):
        TwinScenario(id="x", name="", description="d", variables={"kind": "CUSTOM"})
    with pytest.raises(ValueError):
        TwinScenario.from_dict(
            {"id": "x", "name": "CUSTOM", "description": "d", "variables": "bad"}
        )
    with pytest.raises(ValueError):
        SimulationResult(
            cpu=10,
            memory=10,
            latency=1,
            availability=99,
            stability=90,
            confidence=90,
            risk="nope",  # type: ignore[arg-type]
        )


def test_formatter_empty_library_and_diff() -> None:
    console = Console(record=True, width=80)
    panel = InfrastructureTwinPanel(
        snapshot=demo_snapshot(), scenarios=(), view="library"
    )
    console.print(panel)
    assert (
        "empty" in console.export_text().lower() or "Scenario" in console.export_text()
    )
    panel2 = InfrastructureTwinPanel(snapshot=demo_snapshot(), view="diff")
    console.print(panel2)


def test_from_cloud_naive_timestamp() -> None:
    cloud = seed_demo_cloud().last_snapshot
    assert cloud is not None
    # force naive by rebuilding projection path
    twin = from_cloud_snapshot(cloud, timestamp=datetime(2026, 3, 1, 0, 0, 0))
    assert twin.timestamp.tzinfo is not None
