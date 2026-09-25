"""Explainability bridge — reasoning chains from real graph paths only.

No LLM. No fabricated edges. Paths come exclusively from ``find_path``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from aetheros.bridge.evidence import evidence_for_process, system_evidence
from aetheros.explainability.models import Evidence, ReasoningChain
from aetheros.graph.models import ResourceGraph
from aetheros.graph.queries import find_path, nodes_of_type


@dataclass(frozen=True, slots=True)
class GraphReasoningPath:
    """Immutable path projection for explainability consumers.

    Attributes:
        node_ids: Ordered node ids along a verified graph path.
        labels: Operator-facing names for each hop.
        relations: Edge relationships between consecutive hops.
        evidence: Graph-sourced Evidence for the path endpoints.
    """

    node_ids: tuple[str, ...]
    labels: tuple[str, ...]
    relations: tuple[str, ...]
    evidence: tuple[Evidence, ...]


def reasoning_path(
    graph: ResourceGraph,
    source_id: str,
    target_id: str,
    *,
    now: datetime | None = None,
) -> GraphReasoningPath | None:
    """Build a reasoning path only when ``find_path`` succeeds.

    Returns:
        ``GraphReasoningPath`` or ``None`` when unreachable (never invents hops).
    """

    stamp = now if now is not None else datetime.now(UTC)
    path = find_path(graph, source_id, target_id)
    if path is None:
        return None
    labels: list[str] = []
    relations: list[str] = []
    for index, node_id in enumerate(path):
        node = graph.get_node(node_id)
        labels.append(node.name if node is not None else node_id)
        if index == 0:
            continue
        prev = path[index - 1]
        relation = _edge_relation(graph, prev, node_id)
        relations.append(relation if relation is not None else "LINKED")
    evidence = _path_evidence(graph, path, stamp)
    return GraphReasoningPath(
        node_ids=path,
        labels=tuple(labels),
        relations=tuple(relations),
        evidence=evidence,
    )


def evidence_chain(
    graph: ResourceGraph,
    *,
    process_id: str | None = None,
    now: datetime | None = None,
) -> tuple[Evidence, ...]:
    """Ordered evidence chain for a process or the whole system graph."""

    if process_id is not None:
        return evidence_for_process(graph, process_id, now=now)
    return system_evidence(graph, now=now)


def reasoning_chain_from_path(
    path: GraphReasoningPath,
    *,
    intent_name: str | None = None,
) -> ReasoningChain:
    """Map a GraphReasoningPath into the existing ReasoningChain contract.

    Historical / simulation sections stay empty unless the path itself
    encodes those facts — the bridge never fabricates them.
    """

    hops = " → ".join(path.labels)
    observations = (f"Graph path: {hops}",) + tuple(
        item.description for item in path.evidence
    )
    intent_context: tuple[str, ...] = ()
    if intent_name:
        intent_context = (f"Active intent: {intent_name}",)
    return ReasoningChain(
        observations=observations,
        historical_patterns=(),
        simulation_support=(),
        intent_context=intent_context,
    )


def default_process_to_memory_path(
    graph: ResourceGraph,
    *,
    now: datetime | None = None,
) -> GraphReasoningPath | None:
    """Convenience: first process → memory reasoning path when both exist."""

    processes = nodes_of_type(graph, "Process")
    if not processes or graph.get_node("memory") is None:
        return None
    return reasoning_path(graph, processes[0].id, "memory", now=now)


def _edge_relation(graph: ResourceGraph, source: str, target: str) -> str | None:
    """Return the relationship label for a direct edge, if present."""

    for edge in graph.edges:
        if edge.source == source and edge.target == target:
            return edge.relationship
    return None


def _path_evidence(
    graph: ResourceGraph,
    path: tuple[str, ...],
    stamp: datetime,
) -> tuple[Evidence, ...]:
    """Evidence drawn only from edges along the verified path."""

    from aetheros.bridge.evidence import edge_to_evidence

    items: list[Evidence] = []
    for index in range(1, len(path)):
        src_id, dst_id = path[index - 1], path[index]
        source = graph.get_node(src_id)
        target = graph.get_node(dst_id)
        if source is None or target is None:
            continue
        for edge in graph.edges:
            if edge.source == src_id and edge.target == dst_id:
                items.append(edge_to_evidence(source, edge, target, stamp))
                break
    return tuple(items)
