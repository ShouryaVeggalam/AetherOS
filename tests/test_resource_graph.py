"""Unit tests for Resource Graph Engine (aetheros.graph resource modules)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest
from rich.console import Console
from rich.tree import Tree

from aetheros.graph import (
    ResourceEdge,
    ResourceGraph,
    ResourceGraphPanel,
    ResourceNode,
    assert_valid,
    build_resource_graph,
    dump_path,
    dumps,
    find_path,
    from_dict,
    get_dependents,
    get_neighbors,
    get_process_resources,
    load_path,
    loads,
    subgraph,
    to_dict,
    validate_resource_graph,
)
from aetheros.graph.models import RESOURCE_GRAPH_SCHEMA, EdgeRelation, NodeType
from aetheros.graph.renderer import _add_cpu_branch, _add_simple_branch, _meta
from aetheros.graph.validator import is_valid_edge
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
        disks=(
            DiskSnapshot("/", 100, 40, 60, 40.0),
        ),
        processes=(
            ProcessSnapshot(42, "Cursor", "user", 25.0, 12.0, "running"),
            ProcessSnapshot(7, "python", "user", 10.0, 5.0, "running"),
        ),
        battery=BatterySnapshot(80.0, True, None),
    )


def test_node_and_edge_creation() -> None:
    """Nodes and edges should enforce id/weight invariants."""

    node = ResourceNode("cpu", "CPU", "CPU", (("percent", "10"),), _stamp())
    assert node.id == "cpu"
    edge = ResourceEdge("process:1", "cpu", "USES", 0.5)
    assert edge.relationship == "USES"
    with pytest.raises(ValueError):
        ResourceNode("", "CPU", "x", (), _stamp())
    with pytest.raises(ValueError):
        ResourceNode("cpu", "CPU", "  ", (), _stamp())
    with pytest.raises(ValueError):
        ResourceEdge("", "b", "USES", 0.5)
    with pytest.raises(ValueError):
        ResourceEdge("a", "b", "USES", 2.0)
    lonely = ResourceGraph(nodes=(node,), edges=())
    assert lonely.get_node("missing") is None
    assert lonely.get_node("cpu") is node


def test_builder_from_system_and_telemetry() -> None:
    """Builder should materialise only telemetry-backed nodes."""

    graph = build_resource_graph(_system(), intent_name="Coding", now=_stamp())
    ids = graph.node_ids()
    assert "cpu" in ids
    assert "cpu:core:0" in ids
    assert "memory" in ids
    assert "battery" in ids
    assert "process:42" in ids
    assert "intent:active" in ids
    assert "gpu" not in ids
    assert validate_resource_graph(graph).ok
    assert assert_valid(graph) is graph

    flat = TelemetrySnapshot(
        timestamp=_stamp(),
        cpu_percent=30.0,
        memory_percent=40.0,
        disk_percent=50.0,
        battery_percent=None,
        process_count=1,
        top_processes=("python",),
    )
    flat_graph = build_resource_graph(flat, now=_stamp())
    assert "disk" in flat_graph.node_ids()
    assert "battery" not in flat_graph.node_ids()
    assert any(n.type == "Process" for n in flat_graph.nodes)

    with_battery = TelemetrySnapshot(
        timestamp=_stamp(),
        cpu_percent=30.0,
        memory_percent=40.0,
        disk_percent=50.0,
        battery_percent=70.0,
        process_count=1,
        top_processes=("python",),
    )
    batt_graph = build_resource_graph(with_battery, now=_stamp())
    assert "battery" in batt_graph.node_ids()


def test_validator_rejects_cycles_and_missing() -> None:
    """Validator should surface rich errors for cycles and missing nodes."""

    stamp = _stamp()
    bad = ResourceGraph(
        nodes=(
            ResourceNode("a", "CPU", "A", (), stamp),
            ResourceNode("b", "Memory", "B", (), stamp),
        ),
        edges=(
            ResourceEdge("a", "b", "DEPENDS_ON", 0.5),
            ResourceEdge("b", "a", "DEPENDS_ON", 0.5),
            ResourceEdge("a", "missing", "USES", 0.1),
            ResourceEdge("ghost", "a", "USES", 0.1),
        ),
    )
    result = validate_resource_graph(bad)
    assert result.ok is False
    assert result.error_count >= 2
    codes = {issue.code for issue in result.issues}
    assert "cycle" in codes
    assert "missing_node" in codes
    with pytest.raises(ValueError, match="Invalid ResourceGraph"):
        assert_valid(bad)


def test_validator_duplicate_ids() -> None:
    """Duplicate node ids must fail validation."""

    stamp = _stamp()
    graph = ResourceGraph(
        nodes=(
            ResourceNode("cpu", "CPU", "CPU", (), stamp),
            ResourceNode("cpu", "CPU", "CPU2", (), stamp),
        ),
        edges=(),
    )
    result = validate_resource_graph(graph)
    assert any(issue.code == "duplicate_id" for issue in result.issues)


def test_validator_invalid_types() -> None:
    """Unknown node/edge types and is_valid_edge helper."""

    stamp = _stamp()
    weird_node = ResourceNode("x", cast(NodeType, "Widget"), "X", (), stamp)
    weird_edge = ResourceEdge("x", "x", cast(EdgeRelation, "EATS"), 0.1)
    graph = ResourceGraph(nodes=(weird_node,), edges=(weird_edge,))
    result = validate_resource_graph(graph)
    codes = {issue.code for issue in result.issues}
    assert "invalid_node_type" in codes
    assert "invalid_edge_type" in codes
    good = ResourceEdge("cpu", "memory", "USES", 0.5)
    assert is_valid_edge(good, frozenset({"cpu", "memory"}))
    assert not is_valid_edge(good, frozenset({"cpu"}))


def test_queries_neighbors_path_subgraph_process() -> None:
    """Query helpers should return immutable path and neighbor results."""

    graph = build_resource_graph(_system(), now=_stamp())
    neighbors = get_neighbors(graph, "process:42", direction="out")
    assert any(node.id == "cpu" for node in neighbors)
    inbound = get_neighbors(graph, "cpu", direction="in")
    assert any(node.id == "process:42" for node in inbound)
    both = get_neighbors(graph, "cpu", direction="both")
    assert len(both) >= len(inbound)
    deps = get_dependents(graph, "cpu")
    assert any(node.id == "process:42" for node in deps)
    path = find_path(graph, "process:42", "memory")
    assert path is not None
    assert path[0] == "process:42"
    assert path[-1] == "memory"
    assert find_path(graph, "cpu", "cpu") == ("cpu",)
    resources = get_process_resources(graph, "process:42")
    assert resources
    assert all(edge.source == "process:42" for edge in resources)
    assert get_process_resources(graph, "cpu") == ()
    assert get_process_resources(graph, "missing") == ()
    sub = subgraph(graph, frozenset({"cpu", "memory", "process:42"}))
    assert sub.node_ids() == frozenset({"cpu", "memory", "process:42"})
    assert find_path(graph, "missing", "cpu") is None
    assert find_path(graph, "memory", "process:42") is None
    stamp = _stamp()
    diamond = ResourceGraph(
        nodes=(
            ResourceNode("s", "CPU", "S", (), stamp),
            ResourceNode("a", "Memory", "A", (), stamp),
            ResourceNode("b", "Disk", "B", (), stamp),
            ResourceNode("t", "Network", "T", (), stamp),
        ),
        edges=(
            ResourceEdge("s", "a", "USES", 0.5),
            ResourceEdge("s", "b", "USES", 0.5),
            ResourceEdge("a", "b", "USES", 0.5),
            ResourceEdge("b", "t", "USES", 0.5),
        ),
    )
    assert find_path(diamond, "s", "t") == ("s", "b", "t")


def test_serialization_roundtrip(tmp_path: Path) -> None:
    """JSON export/import should preserve schema, nodes, and edges."""

    graph = build_resource_graph(_system(), intent_name="Coding", now=_stamp())
    payload = to_dict(graph)
    assert payload["schema_version"] == RESOURCE_GRAPH_SCHEMA
    restored = from_dict(payload)
    assert restored.node_ids() == graph.node_ids()
    assert len(restored.edges) == len(graph.edges)
    text = dumps(graph)
    again = loads(text)
    assert again.schema_version == graph.schema_version
    path = dump_path(graph, tmp_path / "graph.json")
    assert load_path(path).get_node("cpu") is not None
    with pytest.raises(ValueError, match="Unsupported"):
        from_dict({"schema_version": "9.9.9", "nodes": [], "edges": []})
    with pytest.raises(ValueError, match="object"):
        loads("[]")
    with pytest.raises(ValueError, match="metadata"):
        from_dict(
            {
                "schema_version": RESOURCE_GRAPH_SCHEMA,
                "nodes": [
                    {
                        "id": "x",
                        "type": "CPU",
                        "name": "X",
                        "metadata": ["bad"],
                        "created_at": _stamp().isoformat(),
                    }
                ],
                "edges": [],
            }
        )
    with pytest.raises(ValueError, match="node type"):
        from_dict(
            {
                "schema_version": RESOURCE_GRAPH_SCHEMA,
                "nodes": [
                    {
                        "id": "x",
                        "type": "Widget",
                        "name": "X",
                        "metadata": {},
                        "created_at": _stamp().isoformat(),
                    }
                ],
                "edges": [],
            }
        )
    with pytest.raises(ValueError, match="edge relationship"):
        from_dict(
            {
                "schema_version": RESOURCE_GRAPH_SCHEMA,
                "nodes": [],
                "edges": [
                    {
                        "source": "a",
                        "target": "b",
                        "relationship": "EATS",
                        "weight": 0.1,
                    }
                ],
            }
        )


def test_renderer_panel() -> None:
    """ResourceGraphPanel should render a System tree."""

    graph = build_resource_graph(_system(), intent_name="Coding", now=_stamp())
    console = Console(record=True, width=100)
    console.print(ResourceGraphPanel(graph=graph))
    text = console.export_text()
    assert "RESOURCE GRAPH" in text or "System" in text
    assert "Cursor" in text
    console.print(ResourceGraphPanel(graph=None))
    assert "idle" in console.export_text().lower() or "Y" in console.export_text()
    empty = ResourceGraph(nodes=(), edges=())
    root = Tree("System")
    _add_cpu_branch(root, empty)
    _add_simple_branch(root, empty, "Memory", "memory")
    lonely = ResourceNode("cpu", "CPU", "CPU", (), _stamp())
    assert _meta(lonely, "percent") == "—"
