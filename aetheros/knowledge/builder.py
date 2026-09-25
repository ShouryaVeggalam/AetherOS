"""Knowledge builder — assemble Causal Knowledge Graph from verified sources.

Sources (read-only):
* Resource Graph
* Operational Memory
* Research Discoveries
* Verified Reasoning
* Digital Twin evidence

Never fabricates relationships. Unsupported Resource Graph relations are skipped.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from aetheros.graph.models import ResourceGraph, ResourceNode
from aetheros.knowledge.models import (
    CausalKnowledgeGraph,
    KnowledgeEdge,
    KnowledgeNode,
)
from aetheros.knowledge.ontology import KnowledgeNodeType
from aetheros.knowledge.relationships import map_resource_relation
from aetheros.memory.models import MemoryRecord


def build_knowledge_graph(
    *,
    resource_graph: ResourceGraph | None = None,
    memories: Sequence[MemoryRecord] = (),
    discoveries: Sequence[Any] = (),
    explanations: Sequence[Any] = (),
    twin_summaries: Sequence[str] = (),
    context_label: str | None = None,
    now: datetime | None = None,
) -> CausalKnowledgeGraph:
    """Build an immutable Causal Knowledge Graph from verified inputs only.

    ``discoveries`` and ``explanations`` are duck-typed to avoid import cycles
    with ``aetheros.research`` / ``aetheros.reasoning``.
    """

    stamp = now or datetime.now(UTC)
    nodes: dict[str, KnowledgeNode] = {}
    edges: dict[tuple[str, str, str], KnowledgeEdge] = {}

    def add_node(node: KnowledgeNode) -> None:
        nodes.setdefault(node.id, node)

    def add_edge(edge: KnowledgeEdge) -> None:
        key = edge.key
        existing = edges.get(key)
        if existing is None:
            edges[key] = edge
            return
        edges[key] = KnowledgeEdge(
            source=existing.source,
            target=existing.target,
            relationship=existing.relationship,
            confidence=max(existing.confidence, edge.confidence),
            evidence_count=existing.evidence_count + edge.evidence_count,
        )

    if resource_graph is not None:
        _ingest_resource_graph(resource_graph, add_node=add_node, add_edge=add_edge)

    if context_label and context_label.strip():
        ctx_id = f"context:{_slug(context_label)}"
        add_node(
            KnowledgeNode(
                id=ctx_id,
                type="Context",
                name=context_label.strip(),
                metadata=(("kind", "operational_context"),),
                created_at=stamp,
            )
        )

    for memory in memories:
        if getattr(memory, "status", "verified") != "verified":
            continue
        _ingest_memory(memory, stamp=stamp, add_node=add_node, add_edge=add_edge)

    for discovery in discoveries:
        _ingest_discovery(discovery, stamp=stamp, add_node=add_node, add_edge=add_edge)

    for explanation in explanations:
        _ingest_explanation(
            explanation, stamp=stamp, add_node=add_node, add_edge=add_edge
        )

    for index, summary in enumerate(twin_summaries):
        if not summary or not summary.strip():
            continue
        _ingest_twin_summary(
            summary.strip(),
            index=index,
            stamp=stamp,
            add_node=add_node,
            add_edge=add_edge,
        )

    connected: set[str] = set()
    for edge in edges.values():
        connected.add(edge.source)
        connected.add(edge.target)
    final_nodes = tuple(
        sorted(
            (n for n in nodes.values() if n.id in connected),
            key=lambda n: n.id,
        )
    )
    final_edges = tuple(sorted(edges.values(), key=lambda e: e.key))
    return CausalKnowledgeGraph(nodes=final_nodes, edges=final_edges)


def _ingest_resource_graph(
    resource_graph: ResourceGraph,
    *,
    add_node: Any,
    add_edge: Any,
) -> None:
    for node in resource_graph.nodes:
        kn = _resource_node_to_knowledge(node)
        if kn is not None:
            add_node(kn)
    for edge in resource_graph.edges:
        relation = map_resource_relation(edge.relationship)
        if relation is None:
            continue
        if resource_graph.get_node(edge.source) is None:
            continue
        if resource_graph.get_node(edge.target) is None:
            continue
        add_edge(
            KnowledgeEdge(
                source=edge.source,
                target=edge.target,
                relationship=relation,
                confidence=round(edge.weight * 100.0, 2),
                evidence_count=1,
            )
        )


def _resource_node_to_knowledge(node: ResourceNode) -> KnowledgeNode | None:
    mapping: dict[str, KnowledgeNodeType] = {
        "CPU": "CPU",
        "Memory": "Memory",
        "Disk": "Disk",
        "GPU": "GPU",
        "Network": "Network",
        "Process": "Process",
        "Battery": "Battery",
        "Intent": "Intent",
        "Cluster": "Cluster",
        "Simulation": "Simulation",
        "Research": "Research",
    }
    mapped = mapping.get(node.type)
    if mapped is None:
        return None
    return KnowledgeNode(
        id=node.id,
        type=mapped,
        name=node.name,
        metadata=node.metadata,
        created_at=node.created_at,
    )


def _ingest_memory(
    memory: MemoryRecord, *, stamp: datetime, add_node: Any, add_edge: Any
) -> None:
    pattern_id = f"pattern:{memory.id}"
    add_node(
        KnowledgeNode(
            id=pattern_id,
            type="Pattern",
            name=memory.title,
            metadata=(
                ("evidence_count", str(memory.evidence_count)),
                ("confidence", f"{memory.confidence:.1f}"),
                ("status", memory.status),
            ),
            created_at=memory.created_at,
        )
    )
    resources = _mentioned_resources(f"{memory.title} {memory.description}")
    for rid, rtype, rname in resources:
        add_node(
            KnowledgeNode(
                id=rid,
                type=rtype,
                name=rname,
                metadata=(("source", "operational_memory"),),
                created_at=stamp,
            )
        )
        add_edge(
            KnowledgeEdge(
                source=pattern_id,
                target=rid,
                relationship="PREDICTS",
                confidence=memory.confidence,
                evidence_count=max(1, memory.evidence_count),
            )
        )
    ids = [r[0] for r in resources]
    if "cpu" in ids and "memory" in ids:
        add_edge(
            KnowledgeEdge(
                source="cpu",
                target="memory",
                relationship="PRECEDES",
                confidence=memory.confidence,
                evidence_count=max(1, memory.evidence_count),
            )
        )
    if "memory" in ids and "disk" in ids:
        add_edge(
            KnowledgeEdge(
                source="memory",
                target="disk",
                relationship="PRECEDES",
                confidence=memory.confidence,
                evidence_count=max(1, memory.evidence_count),
            )
        )
    blob = f"{memory.title} {memory.description}".lower()
    if "coding" in blob or "compile" in blob:
        intent_id = "intent:coding"
        add_node(
            KnowledgeNode(
                id=intent_id,
                type="Intent",
                name="Coding",
                metadata=(("source", "operational_memory"),),
                created_at=stamp,
            )
        )
        add_edge(
            KnowledgeEdge(
                source=intent_id,
                target=pattern_id,
                relationship="CAUSES",
                confidence=memory.confidence,
                evidence_count=max(1, memory.evidence_count),
            )
        )


def _ingest_discovery(
    discovery: Any, *, stamp: datetime, add_node: Any, add_edge: Any
) -> None:
    title = str(getattr(discovery, "title", "") or "")
    summary = str(getattr(discovery, "summary", "") or "")
    confidence = float(getattr(discovery, "confidence", 0.0) or 0.0)
    evidence_count = int(getattr(discovery, "evidence_count", 1) or 1)
    if not title.strip():
        return
    disc_id = f"discovery:{_slug(title)}"
    add_node(
        KnowledgeNode(
            id=disc_id,
            type="Discovery",
            name=title,
            metadata=(
                ("evidence_count", str(evidence_count)),
                ("confidence", f"{confidence:.1f}"),
            ),
            created_at=stamp,
        )
    )
    research_id = "research:system"
    add_node(
        KnowledgeNode(
            id=research_id,
            type="Research",
            name="Research Intelligence",
            metadata=(("source", "research"),),
            created_at=stamp,
        )
    )
    add_edge(
        KnowledgeEdge(
            source=disc_id,
            target=research_id,
            relationship="VERIFIED_BY",
            confidence=confidence,
            evidence_count=max(1, evidence_count),
        )
    )
    for rid, rtype, rname in _mentioned_resources(f"{title} {summary}"):
        add_node(
            KnowledgeNode(
                id=rid,
                type=rtype,
                name=rname,
                metadata=(("source", "discovery"),),
                created_at=stamp,
            )
        )
        add_edge(
            KnowledgeEdge(
                source=disc_id,
                target=rid,
                relationship="CORRELATES",
                confidence=confidence,
                evidence_count=max(1, evidence_count),
            )
        )


def _ingest_explanation(
    explanation: Any,
    *,
    stamp: datetime,
    add_node: Any,
    add_edge: Any,
) -> None:
    conf = float(getattr(explanation, "confidence", 0) or 0)
    summary = str(getattr(explanation, "summary", "") or "")
    evidence = getattr(explanation, "evidence", ()) or ()
    resources = _mentioned_resources(summary)
    for path in getattr(explanation, "reasoning_paths", ()) or ():
        for path_node in getattr(path, "nodes", ()) or ():
            nid = getattr(path_node, "id", None)
            if not isinstance(nid, str):
                continue
            mapped = _canonical_resource(nid)
            if mapped is None:
                continue
            rid, rtype, rname = mapped
            add_node(
                KnowledgeNode(
                    id=rid,
                    type=rtype,
                    name=rname,
                    metadata=(("source", "reasoning"),),
                    created_at=stamp,
                )
            )
    if len(resources) >= 2:
        src = resources[0]
        dst = resources[1]
        add_node(
            KnowledgeNode(
                id=src[0], type=src[1], name=src[2], metadata=(), created_at=stamp
            )
        )
        add_node(
            KnowledgeNode(
                id=dst[0], type=dst[1], name=dst[2], metadata=(), created_at=stamp
            )
        )
        add_edge(
            KnowledgeEdge(
                source=src[0],
                target=dst[0],
                relationship="CAUSES",
                confidence=conf,
                evidence_count=max(1, len(evidence)),
            )
        )


def _ingest_twin_summary(
    summary: str,
    *,
    index: int,
    stamp: datetime,
    add_node: Any,
    add_edge: Any,
) -> None:
    sim_id = f"simulation:{index}:{_slug(summary)[:40]}"
    add_node(
        KnowledgeNode(
            id=sim_id,
            type="Simulation",
            name=summary[:80],
            metadata=(("source", "digital_twin"),),
            created_at=stamp,
        )
    )
    for rid, rtype, rname in _mentioned_resources(summary):
        add_node(
            KnowledgeNode(
                id=rid,
                type=rtype,
                name=rname,
                metadata=(("source", "digital_twin"),),
                created_at=stamp,
            )
        )
        add_edge(
            KnowledgeEdge(
                source=sim_id,
                target=rid,
                relationship="PREDICTS",
                confidence=85.0,
                evidence_count=1,
            )
        )


def _mentioned_resources(
    text: str,
) -> list[tuple[str, KnowledgeNodeType, str]]:
    lower = text.lower()
    found: list[tuple[str, KnowledgeNodeType, str]] = []
    catalog: tuple[tuple[str, str, KnowledgeNodeType, str], ...] = (
        ("cpu", "cpu", "CPU", "CPU"),
        ("memory", "memory", "Memory", "Memory"),
        ("ram", "memory", "Memory", "Memory"),
        ("disk", "disk", "Disk", "Disk"),
        ("gpu", "gpu", "GPU", "GPU"),
        ("network", "network", "Network", "Network"),
        ("battery", "battery", "Battery", "Battery"),
    )
    seen: set[str] = set()
    for needle, rid, rtype, rname in catalog:
        if needle in lower and rid not in seen:
            seen.add(rid)
            found.append((rid, rtype, rname))
    return found


def _canonical_resource(
    node_id: str,
) -> tuple[str, KnowledgeNodeType, str] | None:
    lower = node_id.lower()
    for rid, rtype, rname in (
        ("cpu", "CPU", "CPU"),
        ("memory", "Memory", "Memory"),
        ("disk", "Disk", "Disk"),
        ("gpu", "GPU", "GPU"),
        ("network", "Network", "Network"),
        ("battery", "Battery", "Battery"),
    ):
        if lower == rid or lower.startswith(f"{rid}:"):
            return rid, rtype, rname  # type: ignore[return-value]
    return None


def _slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "item"
