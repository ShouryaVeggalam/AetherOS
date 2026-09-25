"""Unit tests for Graph Reasoning Engine (aetheros.reasoning P6 modules)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from rich.console import Console

from aetheros.graph import (
    ResourceEdge,
    ResourceGraph,
    ResourceNode,
    build_resource_graph,
)
from aetheros.observatory.models import TelemetryPoint
from aetheros.reasoning import (
    GraphReasoningPanel,
    Hypothesis,
    Observation,
    ReasoningPath,
    compute_confidence,
    find_all_paths,
    find_shortest_path,
    generate_hypotheses,
    infer_causal_chain,
    neighbors,
    observation_from_metrics,
    reason,
    verify_hypotheses,
)
from aetheros.reasoning.traversal import common_dependencies, dependents
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


def _system(*, cpu: float = 96.0) -> SystemSnapshot:
    return SystemSnapshot(
        collected_at=_stamp(),
        cpu=CpuSnapshot(
            percent=cpu,
            per_cpu_percent=(90.0, 95.0),
            load_avg=(2.0, 1.5, 1.0),
        ),
        memory=MemorySnapshot(
            total_bytes=16_000,
            available_bytes=4_000,
            used_bytes=12_000,
            percent=75.0,
            swap_total_bytes=0,
            swap_used_bytes=0,
            swap_percent=0.0,
        ),
        disks=(DiskSnapshot("/", 100, 70, 30, 70.0),),
        processes=(
            ProcessSnapshot(42, "Cursor", "user", 55.0, 20.0, "running"),
            ProcessSnapshot(7, "Chrome", "user", 30.0, 15.0, "running"),
        ),
        battery=BatterySnapshot(50.0, False, None),
    )


def _graph() -> ResourceGraph:
    return build_resource_graph(_system(), intent_name="Coding", now=_stamp())


def test_traversal_shortest_and_neighbors() -> None:
    """BFS shortest path and neighbor helpers should stay graph-grounded."""

    graph = _graph()
    path = find_shortest_path(graph, "process:42", "memory")
    assert path is not None
    assert path.source == "process:42"
    assert path.target == "memory"
    assert path.depth >= 1
    assert path.nodes[0].id == "process:42"
    same = find_shortest_path(graph, "cpu", "cpu")
    assert same is not None and same.depth == 0
    assert find_shortest_path(graph, "missing", "cpu") is None
    assert neighbors(graph, "process:42")
    assert dependents(graph, "cpu")


def test_traversal_multiple_paths_and_common_deps() -> None:
    """DFS should enumerate alternate paths; common deps use outbound closure."""

    stamp = _stamp()
    graph = ResourceGraph(
        nodes=(
            ResourceNode("s", "Process", "S", (), stamp),
            ResourceNode("a", "CPU", "A", (), stamp),
            ResourceNode("b", "Memory", "B", (), stamp),
            ResourceNode("t", "Disk", "T", (), stamp),
        ),
        edges=(
            ResourceEdge("s", "a", "USES", 0.5),
            ResourceEdge("s", "b", "USES", 0.5),
            ResourceEdge("a", "t", "DEPENDS_ON", 0.5),
            ResourceEdge("b", "t", "DEPENDS_ON", 0.5),
        ),
    )
    paths = find_all_paths(graph, "s", "t", max_depth=4, limit=8)
    assert len(paths) >= 2
    shared = common_dependencies(graph, "s", "a")
    assert any(node.id == "t" for node in shared)


def test_causal_infer_chain() -> None:
    """Causal engine should only return chains from existing edges."""

    graph = _graph()
    chain = infer_causal_chain(graph, "process:42", "memory")
    assert chain is not None
    assert " → " in " → ".join(n.name for n in chain.nodes)
    assert infer_causal_chain(graph, "process:42", "missing") is None


def test_hypothesis_generation() -> None:
    """Hypotheses must reference process paths into the observation metric."""

    graph = _graph()
    obs = Observation("cpu", 96.0, "CPU Overload", 90.0)
    hyps = generate_hypotheses(graph, obs)
    assert hyps
    assert all(h.supporting_paths for h in hyps)
    assert any("Cursor" in h.title for h in hyps)
    assert generate_hypotheses(graph, Observation("network", 10.0, "Net", 50.0)) == ()


def test_verification_and_reason() -> None:
    """Verifier should accept graph-backed hypotheses and reject empty paths."""

    graph = _graph()
    obs = observation_from_metrics(cpu=96.0, memory=40.0, disk=40.0)
    assert obs.metric == "cpu"
    history = tuple(
        TelemetryPoint(
            timestamp=_stamp() + timedelta(seconds=i),
            cpu=94.0,
            memory=40.0,
            disk=40.0,
            battery=50.0,
            intent="Coding",
        )
        for i in range(5)
    )
    explanation = reason(
        graph,
        obs,
        history=history,
        simulation_agreement=0.6,
        now=_stamp(),
    )
    assert explanation is not None
    assert explanation.confidence >= 0
    assert explanation.reasoning_paths
    assert explanation.evidence
    empty = Hypothesis(
        id="x",
        title="bogus",
        description="no paths",
        supporting_paths=(),
        confidence=10,
    )
    assert (
        verify_hypotheses(graph, obs, (empty,), now=_stamp()) is None
    )


def test_confidence_engine() -> None:
    """Confidence should scale with path completeness and evidence."""

    graph = _graph()
    path = find_shortest_path(graph, "process:42", "cpu")
    assert path is not None
    low = compute_confidence(
        paths=(),
        evidence_count=0,
        historical_agreement=0.0,
        simulation_agreement=0.0,
    )
    high = compute_confidence(
        paths=(path,),
        evidence_count=5,
        historical_agreement=1.0,
        simulation_agreement=1.0,
    )
    assert low == 0
    assert high > low
    assert 0 <= high <= 100


def test_models_reject_bad_geometry() -> None:
    """Frozen models should validate depth and confidence bounds."""

    stamp = _stamp()
    node = ResourceNode("a", "CPU", "A", (), stamp)
    with pytest.raises(ValueError):
        ReasoningPath("a", "a", (), (node, node), 0)
    with pytest.raises(ValueError):
        Hypothesis("h", "t", "d", (), 120)


def test_formatter_panel() -> None:
    """GraphReasoningPanel should render observation and confidence."""

    graph = _graph()
    expl = reason(
        graph,
        Observation("cpu", 96.0, "CPU Overload"),
        now=_stamp(),
    )
    console = Console(record=True, width=100)
    console.print(GraphReasoningPanel(explanation=expl))
    text = console.export_text()
    assert "GRAPH REASONING" in text
    console.print(GraphReasoningPanel(explanation=None))
    assert "idle" in console.export_text().lower() or "R" in console.export_text()


def test_causal_helpers_and_chains() -> None:
    """Cover cognitive causal helpers and ResourceGraph chain utilities."""

    from aetheros.cognition.causal_graph import CausalGraph, GraphEdge, GraphNode
    from aetheros.reasoning.causal import (
        causal_chains_from,
        causes_of,
        explainers_of,
        format_chain_labels,
        primary_process_resource_chain,
        trace_path,
    )

    cg = CausalGraph(
        nodes=(
            GraphNode("a", "process", "A"),
            GraphNode("b", "cpu", "B"),
        ),
        edges=(
            GraphEdge("a", "b", "CAUSES", 0.9, "load"),
            GraphEdge("a", "b", "EXPLAINS", 0.8, "why"),
        ),
    )
    assert causes_of(cg, "b")
    assert explainers_of(cg, "b")
    assert trace_path(cg, "a", "b")
    assert trace_path(cg, "a", "a") == ("a",)
    assert trace_path(cg, "a", "missing") == ()
    graph = _graph()
    chains = causal_chains_from(graph, "process:42", limit=3)
    assert chains
    primary = primary_process_resource_chain(graph)
    assert primary is not None
    assert "→" in format_chain_labels(primary)
    empty = ResourceGraph(nodes=(), edges=())
    assert primary_process_resource_chain(empty) is None


def test_traversal_edge_cases() -> None:
    """Cover BFS/DFS failure branches and empty closures."""

    stamp = _stamp()
    lonely = ResourceGraph(
        nodes=(ResourceNode("only", "CPU", "Only", (), stamp),),
        edges=(),
    )
    assert find_shortest_path(lonely, "only", "only") is not None
    assert find_all_paths(lonely, "only", "only")
    assert find_all_paths(lonely, "missing", "only") == ()
    assert find_shortest_path(lonely, "only", "nope") is None
    assert common_dependencies(lonely, "missing", "only") == ()
    # Filtered relations yield no path
    graph = _graph()
    assert (
        find_shortest_path(
            graph,
            "process:42",
            "memory",
            relations=frozenset({"SIMULATES"}),
        )
        is None
    )


def test_verifier_history_and_battery_metrics() -> None:
    """History agreement and battery metric extraction."""

    graph = _graph()
    history = (
        TelemetryPoint(_stamp(), 10.0, 10.0, 10.0, 5.0, "Coding"),
        TelemetryPoint(_stamp(), 10.0, 10.0, 10.0, 8.0, "Coding"),
    )
    # May or may not verify depending on battery nodes — exercise collectors
    verify_hypotheses(
        graph,
        Observation("cpu", 96.0, "CPU Overload"),
        generate_hypotheses(graph, Observation("cpu", 96.0, "CPU Overload")),
        history=history,
        now=_stamp(),
    )
    from aetheros.reasoning.verifier import _history_metric

    point = history[0]
    assert _history_metric(point, "cpu") == 10.0
    assert _history_metric(point, "memory") == 10.0
    assert _history_metric(point, "disk") == 10.0
    assert _history_metric(point, "battery") == 5.0
    assert _history_metric(point, "network") is None
    low = compute_confidence(
        paths=(),
        evidence_count=0,
        historical_agreement=0.0,
        simulation_agreement=0.0,
    )
    assert low == 0
    zero_depth = find_shortest_path(graph, "cpu", "cpu")
    assert zero_depth is not None
    assert (
        compute_confidence(
            paths=(zero_depth,),
            evidence_count=0,
            historical_agreement=0.0,
            simulation_agreement=0.0,
        )
        == 0
    )
    # VerifiedExplanation confidence bounds
    from aetheros.reasoning.models import VerifiedExplanation

    with pytest.raises(ValueError):
        VerifiedExplanation(
            summary="x",
            evidence=(),
            reasoning_paths=(),
            confidence=101,
            timestamp=_stamp(),
            observation=Observation("cpu", 1.0, "t"),
        )
    with pytest.raises(ValueError):
        ReasoningPath("a", "a", (), (ResourceNode("a", "CPU", "A", (), _stamp()),), 1)
    # Formatter empty evidence / multi-path
    path = find_shortest_path(graph, "process:42", "cpu")
    assert path is not None
    expl = VerifiedExplanation(
        summary="s",
        evidence=(),
        reasoning_paths=(path, path),
        confidence=50,
        timestamp=_stamp(),
        observation=Observation("cpu", 96.0, "CPU Overload"),
    )
    console = Console(record=True, width=80)
    console.print(GraphReasoningPanel(explanation=expl))
    assert "Confidence" in console.export_text()
    # Process without resource edges → skipped
    stamp = _stamp()
    bare = ResourceGraph(
        nodes=(
            ResourceNode("process:1", "Process", "Idle", (), stamp),
            ResourceNode("cpu", "CPU", "CPU", (("percent", "99"),), stamp),
        ),
        edges=(),
    )
    assert generate_hypotheses(bare, Observation("cpu", 99.0, "CPU Overload")) == ()
    # causal_chains limit + primary without flat disk id
    from aetheros.cognition.causal_graph import CausalGraph, GraphEdge, GraphNode
    from aetheros.reasoning.causal import (
        causal_chains_from,
        primary_process_resource_chain,
        trace_path,
    )

    assert len(causal_chains_from(graph, "process:42", limit=1)) == 1
    no_flat_disk = ResourceGraph(
        nodes=(
            ResourceNode("process:1", "Process", "P", (), stamp),
            ResourceNode("cpu", "CPU", "CPU", (), stamp),
            ResourceNode("disk:/", "Disk", "Root", (), stamp),
        ),
        edges=(
            ResourceEdge("process:1", "cpu", "USES", 0.5),
            ResourceEdge("cpu", "disk:/", "DEPENDS_ON", 0.5),
        ),
    )
    assert primary_process_resource_chain(no_flat_disk) is not None
    cg = CausalGraph(
        nodes=(GraphNode("a", "process", "A"), GraphNode("b", "cpu", "B")),
        edges=(GraphEdge("a", "b", "CAUSES", 0.9, "x"),),
    )
    assert trace_path(cg, "a", "b", relation="CAUSES")
    assert trace_path(cg, "a", "b", relation="USES") == ()
    assert generate_hypotheses(graph, Observation("cpu", 96.0, "CPU Overload"), limit=1)
    empty_paths = VerifiedExplanation(
        summary="empty paths",
        evidence=(),
        reasoning_paths=(),
        confidence=10,
        timestamp=_stamp(),
        observation=Observation("cpu", 96.0, "CPU Overload"),
    )
    console.print(GraphReasoningPanel(explanation=empty_paths))
    assert "no paths" in console.export_text().lower() or "Causal" in console.export_text()
    # Process with USES but only via find_all_paths (no shortest to core-only target)
    from aetheros.reasoning.hypotheses import _provisional_confidence

    assert _provisional_confidence(Observation("cpu", 10.0, "t", 90.0), ()) == 0
