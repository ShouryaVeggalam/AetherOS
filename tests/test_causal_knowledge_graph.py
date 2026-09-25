"""Tests for v3 P3 Causal Knowledge Graph."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from rich.console import Console

from aetheros.graph.models import ResourceEdge, ResourceGraph, ResourceNode
from aetheros.knowledge import (
    CORE_ONTOLOGY,
    CausalKnowledgeGraph,
    CausalKnowledgePanel,
    KnowledgeEdge,
    KnowledgeGraphView,
    KnowledgeNode,
    build_knowledge_graph,
    downstream,
    empty_graph,
    find_causes,
    find_effects,
    is_knowledge_node_type,
    is_knowledge_relation,
    map_resource_relation,
    related_discoveries,
    shortest_causal_path,
    upstream,
    validate_graph,
)
from aetheros.knowledge.relationships import (
    dedupe_edge_keys,
    edge_key,
    merge_confidence,
)
from aetheros.knowledge.validator import assert_unique_edges
from aetheros.memory import MemoryEngine


def _stamp(hour: int = 9) -> datetime:
    return datetime(2026, 9, 25, hour, 0, tzinfo=UTC)


def _node(
    nid: str,
    ntype: str = "CPU",
    name: str | None = None,
) -> KnowledgeNode:
    return KnowledgeNode(
        id=nid,
        type=ntype,  # type: ignore[arg-type]
        name=name or nid.upper(),
        metadata=(),
        created_at=_stamp(),
    )


def _edge(
    source: str,
    target: str,
    relationship: str = "CAUSES",
    *,
    confidence: float = 90.0,
    evidence_count: int = 5,
) -> KnowledgeEdge:
    return KnowledgeEdge(
        source=source,
        target=target,
        relationship=relationship,  # type: ignore[arg-type]
        confidence=confidence,
        evidence_count=evidence_count,
    )


# --- ontology / relationships ----------------------------------------------


def test_ontology_catalog_and_legacy_concepts() -> None:
    assert is_knowledge_node_type("CPU")
    assert is_knowledge_node_type("Discovery")
    assert not is_knowledge_node_type("Widget")
    assert len(CORE_ONTOLOGY) >= 1
    assert is_knowledge_relation("CAUSES")
    assert is_knowledge_relation("VERIFIED_BY")
    assert not is_knowledge_relation("TELEPORTS")
    assert map_resource_relation("DEPENDS_ON") == "DEPENDS_ON"
    assert map_resource_relation("COMMUNICATES") is None
    assert edge_key("a", "b", "CAUSES") == ("a", "b", "CAUSES")
    assert dedupe_edge_keys([("a", "b", "CAUSES"), ("a", "b", "CAUSES")]) == (
        ("a", "b", "CAUSES"),
    )
    assert merge_confidence(()) == 0.0
    assert merge_confidence((10.0, 95.0)) == 95.0


def test_model_validation() -> None:
    with pytest.raises(ValueError):
        _node(" ")
    with pytest.raises(ValueError):
        KnowledgeNode(
            id="x",
            type="CPU",
            name=" ",
            metadata=(),
            created_at=_stamp(),
        )
    with pytest.raises(ValueError):
        _edge("a", "a")
    with pytest.raises(ValueError):
        _edge("a", "b", confidence=101.0)
    with pytest.raises(ValueError):
        _edge("a", "b", evidence_count=0)
    with pytest.raises(ValueError):
        KnowledgeEdge(
            source=" ",
            target="b",
            relationship="CAUSES",
            confidence=50.0,
            evidence_count=1,
        )


# --- builder ----------------------------------------------------------------


def test_builder_from_memory_and_resource_graph() -> None:
    engine = MemoryEngine()
    memories = engine.seed_defaults(now=_stamp())
    stamp = _stamp()
    rg = ResourceGraph(
        nodes=(
            ResourceNode("cpu", "CPU", "CPU", (("percent", "80.0"),), stamp),
            ResourceNode("memory", "Memory", "Memory", (("percent", "70.0"),), stamp),
            ResourceNode("disk", "Disk", "Disk", (("percent", "40.0"),), stamp),
        ),
        edges=(
            ResourceEdge("cpu", "memory", "DEPENDS_ON", 0.5),
            ResourceEdge("memory", "disk", "USES", 0.3),
            ResourceEdge("cpu", "disk", "COMMUNICATES", 0.1),  # skipped
        ),
    )
    graph = build_knowledge_graph(
        resource_graph=rg,
        memories=memories,
        discoveries=(
            SimpleNamespace(
                title="CPU precedes memory pressure",
                summary="Verified CPU rise before memory.",
                confidence=91.0,
                evidence_count=12,
            ),
        ),
        explanations=(
            SimpleNamespace(
                confidence=88,
                summary="CPU causes memory pressure",
                evidence=(1, 2, 3),
                reasoning_paths=(SimpleNamespace(nodes=(SimpleNamespace(id="cpu"),)),),
            ),
        ),
        twin_summaries=("Simulation predicts CPU overload", ""),
        context_label="Coding",
        now=stamp,
    )
    assert graph.nodes
    assert graph.edges
    report = validate_graph(graph)
    assert report.ok, report.errors
    assert any(n.type == "Pattern" for n in graph.nodes)
    assert any(n.type == "Discovery" for n in graph.nodes)
    assert any(n.type == "Simulation" for n in graph.nodes)
    # COMMUNICATES skipped
    assert all(e.relationship != "COMMUNICATES" for e in graph.edges)


def test_builder_skips_unverified_memory_and_empty_discovery() -> None:
    stamp = _stamp()
    pending = SimpleNamespace(
        id="p",
        title="Pending",
        description="cpu memory",
        evidence_count=3,
        confidence=50.0,
        status="pending",
        created_at=stamp,
    )
    graph = build_knowledge_graph(
        memories=(pending,),  # type: ignore[arg-type]
        discoveries=(
            SimpleNamespace(title=" ", summary="", confidence=0, evidence_count=1),
        ),
        now=stamp,
    )
    assert graph.nodes == ()
    assert empty_graph().nodes == ()


# --- traversal --------------------------------------------------------------


def test_traversal_apis() -> None:
    nodes = (
        _node("intent", "Intent", "Coding"),
        _node("cpu"),
        _node("memory", "Memory"),
    )
    edges = (
        _edge("intent", "cpu", "CAUSES"),
        _edge("cpu", "memory", "PRECEDES"),
    )
    graph = CausalKnowledgeGraph(nodes=nodes, edges=edges)

    causes = find_causes(graph, "cpu")
    assert causes[0].id == "intent"
    effects = find_effects(graph, "cpu")
    assert effects[0].id == "memory"
    assert {n.id for n in upstream(graph, "memory")} >= {"cpu", "intent"}
    assert {n.id for n in downstream(graph, "intent")} >= {"cpu", "memory"}
    path = shortest_causal_path(graph, "intent", "memory")
    assert [n.id for n in path] == ["intent", "cpu", "memory"]
    assert shortest_causal_path(graph, "memory", "intent") == ()
    assert shortest_causal_path(graph, "missing", "cpu") == ()
    assert shortest_causal_path(graph, "cpu", "cpu")[0].id == "cpu"
    assert find_causes(graph, "missing") == ()
    assert upstream(graph, "nope") == ()
    assert related_discoveries(graph, "cpu") == ()


def test_related_discoveries_bfs() -> None:
    nodes = (
        _node("cpu"),
        _node("d1", "Discovery", "Disc One"),
        _node("research", "Research", "Research"),
    )
    edges = (
        _edge("d1", "cpu", "CORRELATES"),
        _edge("d1", "research", "VERIFIED_BY"),
    )
    graph = CausalKnowledgeGraph(nodes=nodes, edges=edges)
    found = related_discoveries(graph, "cpu")
    assert any(n.id == "d1" for n in found)


# --- validator --------------------------------------------------------------


def test_validator_rejects_cycles_orphans_duplicates() -> None:
    ok = CausalKnowledgeGraph(
        nodes=(_node("a"), _node("b", "Memory", "B")),
        edges=(_edge("a", "b"),),
    )
    assert validate_graph(ok).ok

    cyclic = CausalKnowledgeGraph(
        nodes=(_node("a"), _node("b", "Memory", "B")),
        edges=(_edge("a", "b"), _edge("b", "a")),
    )
    report = validate_graph(cyclic)
    assert not report.ok
    assert any(e.code == "cycle" for e in report.errors)

    orphan = CausalKnowledgeGraph(
        nodes=(_node("a"), _node("lonely", "Disk", "Lonely")),
        edges=(_edge("a", "a"),) if False else (_edge("a", "b"),),  # dangling + orphan
    )
    # rebuild properly
    orphan = CausalKnowledgeGraph(
        nodes=(_node("a"), _node("lonely", "Disk", "Lonely"), _node("b", "Memory")),
        edges=(_edge("a", "b"),),
    )
    report = validate_graph(orphan)
    assert any(e.code == "orphan_node" for e in report.errors)

    dup = CausalKnowledgeGraph(
        nodes=(_node("a"), _node("b", "Memory")),
        edges=(_edge("a", "b"), _edge("a", "b")),
    )
    report = validate_graph(dup)
    assert any(e.code == "duplicate_relationship" for e in report.errors)

    with pytest.raises(ValueError):
        assert_unique_edges((_edge("a", "b"), _edge("a", "b")))


def test_validator_dangling_and_bad_types() -> None:
    bad = CausalKnowledgeGraph(
        nodes=(_node("a"),),
        edges=(_edge("a", "missing"),),
    )
    report = validate_graph(bad)
    assert any(e.code == "dangling_target" for e in report.errors)
    assert report.error_count >= 1


# --- graph view -------------------------------------------------------------


def test_knowledge_graph_view() -> None:
    graph = CausalKnowledgeGraph(
        nodes=(_node("cpu"), _node("memory", "Memory")),
        edges=(_edge("cpu", "memory", "PRECEDES"),),
    )
    view = KnowledgeGraphView.from_graph(graph)
    assert view.node_count() == 2
    assert view.edge_count() == 1
    assert view.get("cpu") is not None
    assert view.outgoing("cpu")
    assert view.incoming("memory")
    assert view.nodes_by_type("CPU")[0].id == "cpu"
    assert graph.get_node("cpu") is not None
    assert graph.node_ids() == frozenset({"cpu", "memory"})
    assert graph.outgoing("cpu")
    assert graph.incoming("memory")


# --- formatter --------------------------------------------------------------


def test_formatter_views() -> None:
    engine = MemoryEngine()
    memories = engine.seed_defaults(now=_stamp())
    graph = build_knowledge_graph(memories=memories, now=_stamp())
    console = Console(record=True, width=100)
    console.print(CausalKnowledgePanel())
    assert "idle" in console.export_text().lower() or "CAUSAL" in console.export_text()

    for view in ("causal", "ontology", "discoveries", "relationships", "evidence"):
        console = Console(record=True, width=100)
        console.print(CausalKnowledgePanel(graph=graph, view=view))
        out = console.export_text()
        assert "CAUSAL KNOWLEDGE GRAPH" in out


def test_package_exports_stable() -> None:
    from aetheros.knowledge import (
        concepts_by_domain,
        edges_for_workload,
        get_concept,
        get_resource_type,
    )
    from aetheros.knowledge.resource_types import get_resource_type as grt
    from aetheros.knowledge.workload_graph import WorkloadEdge

    assert get_resource_type("cpu").label == "CPU"
    assert edges_for_workload("workload.coding")
    assert concepts_by_domain("workload")
    assert get_concept("workload.coding").label == "Coding"
    with pytest.raises(KeyError):
        get_concept("missing.concept")
    with pytest.raises(KeyError):
        grt("not-a-kind")
    with pytest.raises(ValueError):
        WorkloadEdge("workload.coding", "CAUSES", "cpu", 1.5, "bad")


def test_formatter_empty_sections_and_fallback_path() -> None:
    # Graph with only a Discovery (no intent/cpu chain) hits fallbacks.
    graph = CausalKnowledgeGraph(
        nodes=(_node("d1", "Discovery", "Only Discovery"), _node("r", "Research", "R")),
        edges=(_edge("d1", "r", "VERIFIED_BY"),),
    )
    console = Console(record=True, width=100)
    console.print(CausalKnowledgePanel(graph=graph, view="causal"))
    assert "CAUSAL" in console.export_text()
    console = Console(record=True, width=100)
    console.print(CausalKnowledgePanel(graph=graph, view="discoveries"))
    assert "Only Discovery" in console.export_text()
    console = Console(record=True, width=100)
    console.print(CausalKnowledgePanel(graph=graph, view="relationships"))
    assert "VERIFIED_BY" in console.export_text()
    # Empty discoveries list path when no Discovery nodes
    bare = CausalKnowledgeGraph(
        nodes=(_node("cpu"), _node("memory", "Memory")),
        edges=(_edge("cpu", "memory", "USES", confidence=40.0),),
    )
    console = Console(record=True, width=100)
    console.print(CausalKnowledgePanel(graph=bare, view="discoveries"))
    assert "(none)" in console.export_text() or "Discoveries" in console.export_text()


def test_builder_merge_duplicate_edges_and_memory_disk_chain() -> None:
    stamp = _stamp()
    # Two memories mentioning compile/disk to exercise merge + disk PRECEDES.
    from aetheros.memory.models import MemoryRecord

    mem = MemoryRecord(
        id="m_disk",
        title="Compile Disk Contention",
        description="Compile workloads frequently create disk contention with memory pressure.",
        evidence_count=10,
        confidence=88.0,
        created_at=stamp,
        last_verified=stamp,
        sources=("telemetry_history", "reasoning"),
        status="verified",
        evidence_ids=("e1",),
    )
    rg = ResourceGraph(
        nodes=(
            ResourceNode("cpu", "CPU", "CPU", (), stamp),
            ResourceNode("memory", "Memory", "Memory", (), stamp),
            ResourceNode("disk", "Disk", "Disk", (), stamp),
        ),
        edges=(
            ResourceEdge("cpu", "memory", "DEPENDS_ON", 0.4),
            ResourceEdge(
                "cpu", "memory", "DEPENDS_ON", 0.6
            ),  # merge via builder ingest twice? same key from one graph - second overwrites in resource as separate edges with same key - builder merges
        ),
    )
    # Resource graph can contain duplicate relation keys; builder merges.
    graph = build_knowledge_graph(resource_graph=rg, memories=(mem,), now=stamp)
    assert any(e.relationship == "PRECEDES" for e in graph.edges)
    keys = [e.key for e in graph.edges]
    assert len(keys) == len(set(keys))


def test_traversal_skips_non_causal_and_missing_nodes() -> None:
    graph = CausalKnowledgeGraph(
        nodes=(_node("a"), _node("b", "Memory")),
        edges=(_edge("a", "b", "USES"),),
    )
    assert find_causes(graph, "b") == ()
    assert find_effects(graph, "a") == ()
    # Custom relations include USES
    assert find_effects(graph, "a", relations=("USES",))
    assert related_discoveries(graph, "missing") == ()


def test_validator_unsupported_edge_and_duplicate_node() -> None:
    from dataclasses import replace

    bad_rel = replace(_edge("a", "b"), relationship="NOPE")  # type: ignore[arg-type]
    bad = CausalKnowledgeGraph(
        nodes=(_node("a"), _node("b", "Memory")),
        edges=(bad_rel,),
    )
    report = validate_graph(bad)
    assert any(e.code == "unsupported_edge_type" for e in report.errors)

    bad_type = replace(_node("a"), type="Widget")  # type: ignore[arg-type]
    bad_nodes = CausalKnowledgeGraph(
        nodes=(bad_type, _node("b", "Memory")),
        edges=(_edge("a", "b"),),
    )
    report = validate_graph(bad_nodes)
    assert any(e.code == "invalid_ontology" for e in report.errors)

    dangling = CausalKnowledgeGraph(
        nodes=(_node("b", "Memory"),),
        edges=(_edge("missing", "b"),),
    )
    report = validate_graph(dangling)
    assert any(e.code == "dangling_source" for e in report.errors)

    dup_nodes = CausalKnowledgeGraph(
        nodes=(_node("a"), _node("a"), _node("b", "Memory")),
        edges=(_edge("a", "b"),),
    )
    report = validate_graph(dup_nodes)
    assert any(e.code == "duplicate_node" for e in report.errors)


def test_graph_stamp_now() -> None:
    from aetheros.knowledge.graph import stamp_now

    assert stamp_now().tzinfo is not None
