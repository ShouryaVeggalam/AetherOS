"""Causal reasoning helpers over the cognitive causal graph."""

from __future__ import annotations

from aetheros.cognition.causal_graph import CausalGraph, GraphEdge
from aetheros.knowledge.resource_types import RelationKind


def causes_of(graph: CausalGraph, target_id: str) -> tuple[GraphEdge, ...]:
    """Return CAUSES edges pointing at a target node."""

    return tuple(e for e in graph.incoming(target_id) if e.relation == "CAUSES")


def explainers_of(graph: CausalGraph, target_id: str) -> tuple[GraphEdge, ...]:
    """Return EXPLAINS edges pointing at a target node."""

    return tuple(e for e in graph.incoming(target_id) if e.relation == "EXPLAINS")


def trace_path(
    graph: CausalGraph,
    source_id: str,
    target_id: str,
    *,
    relation: RelationKind | None = None,
    limit: int = 8,
) -> tuple[str, ...]:
    """BFS path of node ids from source to target (empty if none)."""

    if source_id == target_id:
        return (source_id,)
    queue: list[tuple[str, tuple[str, ...]]] = [(source_id, (source_id,))]
    seen = {source_id}
    while queue and len(seen) < 64:
        current, path = queue.pop(0)
        for edge in graph.outgoing(current):
            if relation is not None and edge.relation != relation:
                continue
            nxt = edge.target_id
            if nxt in seen:
                continue
            new_path = path + (nxt,)
            if nxt == target_id:
                return new_path
            if len(new_path) <= limit:
                seen.add(nxt)
                queue.append((nxt, new_path))
    return ()
