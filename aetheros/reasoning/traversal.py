"""Graph Reasoning traversal — BFS / DFS over ResourceGraph.

Never mutates the graph. Paths are materialised as new immutable tuples.
"""

from __future__ import annotations

from aetheros.graph.models import (
    EDGE_RELATIONS,
    ResourceEdge,
    ResourceGraph,
    ResourceNode,
)
from aetheros.graph.queries import get_dependents, get_neighbors
from aetheros.reasoning.models import ReasoningPath

DEFAULT_RELATIONS: frozenset[str] = frozenset(EDGE_RELATIONS)


def neighbors(
    graph: ResourceGraph,
    node_id: str,
    *,
    direction: str = "out",
) -> tuple[ResourceNode, ...]:
    """Return neighboring nodes (delegates to graph queries)."""

    return get_neighbors(graph, node_id, direction=direction)


def dependents(graph: ResourceGraph, node_id: str) -> tuple[ResourceNode, ...]:
    """Return nodes with DEPENDS_ON or USES edges into ``node_id``."""

    return get_dependents(graph, node_id)


def find_shortest_path(
    graph: ResourceGraph,
    source: str,
    target: str,
    *,
    relations: frozenset[str] | None = None,
) -> ReasoningPath | None:
    """BFS shortest path of typed edges, or ``None`` if unreachable."""

    allowed = relations if relations is not None else DEFAULT_RELATIONS
    if source not in graph.node_ids() or target not in graph.node_ids():
        return None
    if source == target:
        node = graph.get_node(source)
        if node is None:  # pragma: no cover
            return None
        return ReasoningPath(
            source=source,
            target=target,
            edges=(),
            nodes=(node,),
            depth=0,
        )
    adjacency = _adjacency(graph, allowed)
    queue: list[str] = [source]
    parents: dict[str, tuple[str, ResourceEdge] | None] = {source: None}
    while queue:
        current = queue.pop(0)
        for edge in adjacency.get(current, ()):
            nxt = edge.target
            if nxt in parents:
                continue
            parents[nxt] = (current, edge)
            if nxt == target:
                return _materialise_path(graph, parents, source, target)
            queue.append(nxt)
    return None


def find_all_paths(
    graph: ResourceGraph,
    source: str,
    target: str,
    *,
    relations: frozenset[str] | None = None,
    max_depth: int = 8,
    limit: int = 16,
) -> tuple[ReasoningPath, ...]:
    """DFS exhaustive paths up to ``max_depth`` / ``limit`` (acyclic)."""

    allowed = relations if relations is not None else DEFAULT_RELATIONS
    if source not in graph.node_ids() or target not in graph.node_ids():
        return ()
    if source == target:
        node = graph.get_node(source)
        if node is None:  # pragma: no cover
            return ()
        return (
            ReasoningPath(
                source=source,
                target=target,
                edges=(),
                nodes=(node,),
                depth=0,
            ),
        )
    adjacency = _adjacency(graph, allowed)
    found: list[ReasoningPath] = []

    def dfs(
        current: str,
        edge_stack: list[ResourceEdge],
        visited: set[str],
    ) -> None:
        if len(found) >= limit:
            return
        if current == target and edge_stack:
            path = _from_edges(graph, source, target, tuple(edge_stack))
            if path is not None:
                found.append(path)
            return
        if len(edge_stack) >= max_depth:  # pragma: no cover
            return
        for edge in adjacency.get(current, ()):
            nxt = edge.target
            if nxt in visited:
                continue
            edge_stack.append(edge)
            visited.add(nxt)
            dfs(nxt, edge_stack, visited)
            visited.remove(nxt)
            edge_stack.pop()

    dfs(source, [], {source})
    return tuple(found)


def common_dependencies(
    graph: ResourceGraph,
    node_a: str,
    node_b: str,
) -> tuple[ResourceNode, ...]:
    """Nodes reachable as outbound dependencies from both anchors."""

    deps_a = {node.id for node in _outbound_closure(graph, node_a)}
    deps_b = {node.id for node in _outbound_closure(graph, node_b)}
    shared = deps_a & deps_b
    return tuple(node for node in graph.nodes if node.id in shared)


def _adjacency(
    graph: ResourceGraph,
    allowed: frozenset[str],
) -> dict[str, tuple[ResourceEdge, ...]]:
    """Build outbound adjacency filtered by relationship set."""

    buckets: dict[str, list[ResourceEdge]] = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        if edge.relationship not in allowed:
            continue
        if edge.source in buckets:
            buckets[edge.source].append(edge)
    return {key: tuple(value) for key, value in buckets.items()}


def _materialise_path(
    graph: ResourceGraph,
    parents: dict[str, tuple[str, ResourceEdge] | None],
    source: str,
    target: str,
) -> ReasoningPath | None:
    """Rebuild a ReasoningPath from BFS parent pointers."""

    edges_rev: list[ResourceEdge] = []
    current = target
    while current != source:
        parent = parents.get(current)
        if parent is None:  # pragma: no cover
            return None
        prev, edge = parent
        edges_rev.append(edge)
        current = prev
    edges_rev.reverse()
    return _from_edges(graph, source, target, tuple(edges_rev))


def _from_edges(
    graph: ResourceGraph,
    source: str,
    target: str,
    edges: tuple[ResourceEdge, ...],
) -> ReasoningPath | None:
    """Assemble nodes for an ordered edge list."""

    if not edges:
        node = graph.get_node(source)
        if node is None:  # pragma: no cover
            return None
        return ReasoningPath(
            source=source,
            target=target,
            edges=(),
            nodes=(node,),
            depth=0,
        )
    node_ids = [edges[0].source]
    for edge in edges:
        node_ids.append(edge.target)
    nodes: list[ResourceNode] = []
    for node_id in node_ids:
        node = graph.get_node(node_id)
        if node is None:  # pragma: no cover
            return None
        nodes.append(node)
    return ReasoningPath(
        source=source,
        target=target,
        edges=edges,
        nodes=tuple(nodes),
        depth=len(edges),
    )


def _outbound_closure(
    graph: ResourceGraph,
    start: str,
    *,
    limit: int = 32,
) -> tuple[ResourceNode, ...]:
    """BFS set of nodes reachable outbound from ``start`` (excluding start)."""

    if start not in graph.node_ids():
        return ()
    adjacency = _adjacency(graph, DEFAULT_RELATIONS)
    seen: set[str] = set()
    queue = [start]
    while queue and len(seen) < limit:
        current = queue.pop(0)
        for edge in adjacency.get(current, ()):
            if edge.target in seen or edge.target == start:
                continue
            seen.add(edge.target)
            queue.append(edge.target)
    return tuple(node for node in graph.nodes if node.id in seen)
