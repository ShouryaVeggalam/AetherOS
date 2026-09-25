"""Unit tests for Graph Intelligence Bridge (aetheros.bridge)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from aetheros.bridge import (
    GraphBridge,
    aggregate_percent,
    create_snapshot,
    default_process_to_memory_path,
    diff_snapshots,
    evidence_chain,
    prediction_inputs,
    reasoning_chain_from_path,
    reasoning_path,
    system_evidence,
)
from aetheros.graph import (
    ResourceEdge,
    ResourceGraph,
    ResourceNode,
    build_resource_graph,
)
from aetheros.telemetry.models import (
    BatterySnapshot,
    CpuSnapshot,
    DiskSnapshot,
    MemorySnapshot,
    ProcessSnapshot,
    SystemSnapshot,
)


def _stamp() -> datetime:
    return datetime(2026, 1, 1, tzinfo=UTC)


def _system() -> SystemSnapshot:
    return SystemSnapshot(
        collected_at=_stamp(),
        cpu=CpuSnapshot(
            percent=40.0,
            per_cpu_percent=(20.0, 60.0),
            load_avg=(0.5, 0.4, 0.3),
        ),
        memory=MemorySnapshot(
            total_bytes=16_000,
            available_bytes=8_000,
            used_bytes=8_000,
            percent=50.0,
            swap_total_bytes=0,
            swap_used_bytes=0,
            swap_percent=0.0,
        ),
        disks=(DiskSnapshot("/", 100, 40, 60, 40.0),),
        processes=(
            ProcessSnapshot(42, "Cursor", "user", 25.0, 12.0, "running"),
            ProcessSnapshot(7, "python", "user", 10.0, 5.0, "running"),
        ),
        battery=BatterySnapshot(80.0, True, None),
    )


def _graph() -> ResourceGraph:
    return build_resource_graph(_system(), intent_name="Coding", now=_stamp())


def test_bridge_adapter_context_and_process() -> None:
    """GraphBridge should expose context, neighbors, and process resources."""

    bridge = GraphBridge(_graph(), historical_window=30)
    ctx = bridge.current_context(now=_stamp())
    assert ctx.active_intent == "Coding"
    assert ctx.foreground_process == "Cursor"
    assert ctx.battery_state == "80.0"
    assert ctx.simulation_active is False
    assert ctx.cluster_health == "unknown"
    assert bridge.active_intent() == "Coding"
    view = bridge.get_process_resources(42)
    assert view is not None
    assert view.process_name == "Cursor"
    assert view.edges
    assert bridge.get_process_resources(9999) is None
    neighbors = bridge.get_resource_neighbors("process:42")
    assert any(node.id == "cpu" for node in neighbors)
    assert bridge.simulation_state().active is False


def test_evidence_conversion() -> None:
    """Process→resource edges become Evidence with source=graph."""

    bridge = GraphBridge(_graph())
    items = bridge.system_evidence(now=_stamp())
    assert items
    assert all(item.source == "graph" for item in items)
    assert any("Cursor" in item.description for item in items)
    assert any(item.metric == "cpu_usage" for item in items)
    proc = bridge.process_evidence("process:42", now=_stamp())
    assert proc
    assert all(item.source == "graph" for item in proc)
    assert evidence_chain(_graph(), process_id="process:42", now=_stamp())
    assert system_evidence(_graph(), now=_stamp(), limit=2)
    empty = ResourceGraph(nodes=(), edges=())
    assert system_evidence(empty) == ()


def test_prediction_context() -> None:
    """PredictionContext should project typed node sets without inventing GPUs."""

    bridge = GraphBridge(_graph(), historical_window=45)
    ctx = bridge.prediction_inputs()
    assert ctx.historical_window == 45
    assert ctx.intent == "Coding"
    assert ctx.cpu_nodes
    assert ctx.memory_nodes
    assert ctx.gpu_nodes == ()
    assert ctx.active_processes
    avg = aggregate_percent(ctx.cpu_nodes)
    assert avg is not None
    assert avg > 0
    with pytest.raises(ValueError):
        prediction_inputs(_graph(), historical_window=-1)
    lonely = ResourceNode("x", "Research", "R", (("note", "n/a"),), _stamp())
    assert aggregate_percent((lonely,)) is None


def test_explainability_paths() -> None:
    """Reasoning paths require real find_path success; no fabricated hops."""

    bridge = GraphBridge(_graph())
    path = bridge.reasoning_path("process:42", "memory", now=_stamp())
    assert path is not None
    assert path.node_ids[0] == "process:42"
    assert path.node_ids[-1] == "memory"
    assert path.labels
    assert path.evidence
    chain = reasoning_chain_from_path(path, intent_name="Coding")
    assert chain.observations
    assert chain.intent_context
    assert bridge.reasoning_path("process:42", "missing") is None
    assert default_process_to_memory_path(_graph(), now=_stamp()) is not None
    empty = ResourceGraph(nodes=(), edges=())
    assert default_process_to_memory_path(empty) is None
    assert reasoning_path(_graph(), "cpu", "cpu", now=_stamp()) is not None


def test_snapshot_cloning_and_diff() -> None:
    """Snapshots and clones are immutable; diffs report topology changes."""

    bridge = GraphBridge(_graph())
    snap_a = bridge.create_snapshot(now=_stamp())
    cloned = bridge.clone_graph()
    assert cloned.node_ids() == bridge.graph.node_ids()
    assert cloned is not bridge.graph
    snap_b = create_snapshot(cloned, now=_stamp())
    assert diff_snapshots(snap_a, snap_b).empty
    stamp = _stamp()
    lean = ResourceGraph(
        nodes=(ResourceNode("cpu", "CPU", "CPU", (), stamp),),
        edges=(),
    )
    snap_c = create_snapshot(lean, now=stamp)
    diff = bridge.diff_snapshots(snap_c, snap_a)
    assert "memory" in diff.added_nodes or len(diff.added_nodes) > 0
    assert not diff.empty
    # Identity edge key coverage via explicit edge add
    richer = ResourceGraph(
        nodes=(
            ResourceNode("cpu", "CPU", "CPU", (), stamp),
            ResourceNode("memory", "Memory", "Memory", (), stamp),
        ),
        edges=(ResourceEdge("cpu", "memory", "DEPENDS_ON", 0.5),),
    )
    d2 = diff_snapshots(create_snapshot(lean), create_snapshot(richer))
    assert any("DEPENDS_ON" in key for key in d2.added_edges)


def test_cluster_and_simulation_nodes() -> None:
    """Cluster / Simulation summaries reflect only real typed nodes."""

    stamp = _stamp()
    base = _graph()
    with_cluster = ResourceGraph(
        nodes=base.nodes
        + (
            ResourceNode("cluster:1", "Cluster", "Node A", (), stamp),
            ResourceNode("sim:1", "Simulation", "What-if", (), stamp),
        ),
        edges=base.edges,
        schema_version=base.schema_version,
    )
    bridge = GraphBridge(with_cluster)
    summary = bridge.get_cluster_summary()
    assert summary.node_count == 1
    assert summary.health == "present"
    assert bridge.simulation_state().active is True
    ctx = bridge.current_context(now=stamp)
    assert ctx.simulation_active is True
    assert ctx.cluster_health == "present"


def test_system_evidence_fallback_without_processes() -> None:
    """Non-process graphs still emit edge-backed evidence."""

    stamp = _stamp()
    graph = ResourceGraph(
        nodes=(
            ResourceNode("cpu", "CPU", "CPU", (("percent", "10"),), stamp),
            ResourceNode("memory", "Memory", "Memory", (("percent", "20"),), stamp),
            ResourceNode("research:1", "Research", "Lab", (("percent", "na"),), stamp),
        ),
        edges=(
            ResourceEdge("cpu", "memory", "ALLOCATES", 0.4),
            ResourceEdge("cpu", "ghost", "USES", 0.1),
            ResourceEdge("cpu", "research:1", "PREDICTS", 0.2),
        ),
    )
    items = system_evidence(graph, now=stamp, limit=1)
    assert len(items) == 1
    assert "allocates" in items[0].description.lower()
    more = system_evidence(
        ResourceGraph(
            nodes=graph.nodes[:2],
            edges=(ResourceEdge("cpu", "memory", "COMMUNICATES", 0.2),),
        ),
        now=stamp,
    )
    assert "communicates" in more[0].description.lower()
    from aetheros.bridge.evidence import edge_to_evidence, evidence_for_process

    assert evidence_for_process(graph, "cpu") == ()
    assert evidence_for_process(graph, "missing") == ()
    dangling = ResourceGraph(
        nodes=(ResourceNode("p", "Process", "P", (), stamp),),
        edges=(ResourceEdge("p", "missing", "USES", 0.1),),
    )
    assert evidence_for_process(dangling, "p", now=stamp) == ()
    bad_meta = ResourceNode("n", "Intent", "I", (("percent", "x"),), stamp)
    ev = edge_to_evidence(
        bad_meta,
        ResourceEdge("n", "n", "SIMULATES", 0.1),
        bad_meta,
        stamp,
    )
    assert ev.value == 0.0
    assert ev.metric == "intent_link"


def test_bridge_lookups_and_aggregates() -> None:
    """Name-based process lookup, evidence_chain facade, aggregate edge cases."""

    bridge = GraphBridge(_graph())
    by_name = bridge.get_process_resources("Cursor")
    assert by_name is not None
    assert by_name.process_id == "process:42"
    by_id = bridge.get_process_resources("process:42")
    assert by_id is not None
    assert bridge.evidence_chain(now=_stamp())
    assert bridge.evidence_chain(process_id="process:42", now=_stamp())
    assert evidence_chain(_graph(), now=_stamp())
    stamp = _stamp()
    weird = ResourceNode(
        "r",
        "Research",
        "R",
        (
            ("percent", "bad"),
            ("other", "1"),
        ),
        stamp,
    )
    assert aggregate_percent((weird,)) is None
    ok = ResourceNode("m", "Memory", "M", (("percent", "10"),), stamp)
    assert aggregate_percent((ok, weird)) == 10.0
    no_batt = build_resource_graph(
        SystemSnapshot(
            collected_at=stamp,
            cpu=CpuSnapshot(10.0, (10.0,), (0.1, 0.1, 0.1)),
            memory=MemorySnapshot(1, 1, 0, 0.0, 0, 0, 0.0),
            disks=(),
            processes=(),
            battery=None,
        ),
        now=stamp,
    )
    ctx = GraphBridge(no_batt).current_context(now=stamp)
    assert ctx.battery_state is None
    # Path with a hop missing a direct edge uses LINKED fallback via synthetic path evidence skip
    from aetheros.bridge.explainability import reasoning_chain_from_path as rcf

    path = bridge.reasoning_path("process:42", "memory", now=stamp)
    assert path is not None
    assert rcf(path).intent_context == ()
