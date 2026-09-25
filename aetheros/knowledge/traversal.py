"""Causal Knowledge Graph traversal — BFS/DFS over verified edges.

All helpers are pure: never mutate the graph. Causal helpers default to
CAUSES / PRECEDES / PREDICTS relations unless ``relations`` is supplied.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence

from aetheros.knowledge.models import CausalKnowledgeGraph, KnowledgeEdge, KnowledgeNode
from aetheros.knowledge.relationships import CAUSAL_RELATIONS, KnowledgeRelation


def find_causes(
    graph: CausalKnowledgeGraph,
    node_id: str,
    *,
    relations: Sequence[KnowledgeRelation] | None = None,
) -> tuple[KnowledgeNode, ...]:
    """Return direct causal predecessors of ``node_id``."""

    allowed = frozenset(relations) if relations is not None else CAUSAL_RELATIONS
    nodes: list[KnowledgeNode] = []
    for edge in graph.incoming(node_id):
        if edge.relationship not in allowed:
            continue
        node = graph.get_node(edge.source)
        if node is not None:
            nodes.append(node)
    return tuple(nodes)


def find_effects(
    graph: CausalKnowledgeGraph,
    node_id: str,
    *,
    relations: Sequence[KnowledgeRelation] | None = None,
) -> tuple[KnowledgeNode, ...]:
    """Return direct causal successors of ``node_id``."""

    allowed = frozenset(relations) if relations is not None else CAUSAL_RELATIONS
    nodes: list[KnowledgeNode] = []
    for edge in graph.outgoing(node_id):
        if edge.relationship not in allowed:
            continue
        node = graph.get_node(edge.target)
        if node is not None:
            nodes.append(node)
    return tuple(nodes)


def upstream(
    graph: CausalKnowledgeGraph,
    node_id: str,
    *,
    relations: Sequence[KnowledgeRelation] | None = None,
    limit: int = 64,
) -> tuple[KnowledgeNode, ...]:
    """BFS ancestors following reverse causal edges."""

    return _bfs(
        graph,
        start=node_id,
        forward=False,
        relations=relations,
        limit=limit,
    )


def downstream(
    graph: CausalKnowledgeGraph,
    node_id: str,
    *,
    relations: Sequence[KnowledgeRelation] | None = None,
    limit: int = 64,
) -> tuple[KnowledgeNode, ...]:
    """BFS descendants following causal edges."""

    return _bfs(
        graph,
        start=node_id,
        forward=True,
        relations=relations,
        limit=limit,
    )


def shortest_causal_path(
    graph: CausalKnowledgeGraph,
    source: str,
    target: str,
    *,
    relations: Sequence[KnowledgeRelation] | None = None,
) -> tuple[KnowledgeNode, ...]:
    """BFS shortest path along causal relations (empty if none)."""

    if source == target:
        node = graph.get_node(source)
        return (node,) if node is not None else ()
    if graph.get_node(source) is None or graph.get_node(target) is None:
        return ()

    allowed = frozenset(relations) if relations is not None else CAUSAL_RELATIONS
    parent: dict[str, str | None] = {source: None}
    queue: deque[str] = deque([source])
    found = False
    while queue:
        current = queue.popleft()
        if current == target:
            found = True
            break
        for edge in graph.outgoing(current):
            if edge.relationship not in allowed:
                continue
            nxt = edge.target
            if nxt in parent:
                continue
            parent[nxt] = current
            queue.append(nxt)
    if not found:
        return ()
    chain: list[str] = []
    cursor: str | None = target
    while cursor is not None:
        chain.append(cursor)
        cursor = parent[cursor]
    chain.reverse()
    nodes: list[KnowledgeNode] = []
    for nid in chain:
        node = graph.get_node(nid)
        if node is not None:
            nodes.append(node)
    return tuple(nodes)


def related_discoveries(
    graph: CausalKnowledgeGraph,
    node_id: str,
) -> tuple[KnowledgeNode, ...]:
    """Return Discovery nodes linked to ``node_id`` (any relation, BFS depth 2)."""

    if graph.get_node(node_id) is None:
        return ()
    found: list[KnowledgeNode] = []
    seen: set[str] = {node_id}
    queue: deque[tuple[str, int]] = deque([(node_id, 0)])
    while queue:
        current, depth = queue.popleft()
        if depth >= 2:
            continue
        neighbors = list(graph.outgoing(current)) + list(graph.incoming(current))
        for edge in neighbors:
            nxt = edge.target if edge.source == current else edge.source
            if nxt in seen:
                continue
            seen.add(nxt)
            node = graph.get_node(nxt)
            if node is None:
                continue
            if node.type == "Discovery":
                found.append(node)
            queue.append((nxt, depth + 1))
    found.sort(key=lambda n: n.name)
    return tuple(found)


def _bfs(
    graph: CausalKnowledgeGraph,
    *,
    start: str,
    forward: bool,
    relations: Sequence[KnowledgeRelation] | None,
    limit: int,
) -> tuple[KnowledgeNode, ...]:
    if graph.get_node(start) is None:
        return ()
    allowed = frozenset(relations) if relations is not None else CAUSAL_RELATIONS
    seen: set[str] = {start}
    order: list[KnowledgeNode] = []
    queue: deque[str] = deque([start])
    while queue and len(order) < max(0, limit):
        current = queue.popleft()
        edges: Sequence[KnowledgeEdge]
        if forward:
            edges = graph.outgoing(current)
        else:
            edges = graph.incoming(current)
        for edge in edges:
            if edge.relationship not in allowed:
                continue
            nxt = edge.target if forward else edge.source
            if nxt in seen:
                continue
            seen.add(nxt)
            node = graph.get_node(nxt)
            if node is None:
                continue
            order.append(node)
            queue.append(nxt)
            if len(order) >= max(0, limit):
                break
    return tuple(order)
