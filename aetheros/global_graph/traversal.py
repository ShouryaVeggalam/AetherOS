"""Traversal engine for the Global Knowledge Graph (read-only).

find_region · find_cluster · upstream · downstream · shortest_path ·
related_discoveries · impact_analysis

All returns are immutable. Never mutates the graph.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass

from aetheros.global_graph.models import GlobalEdge, GlobalKnowledgeGraph, GlobalNode


@dataclass(frozen=True, slots=True)
class PathResult:
    """Immutable path between two nodes."""

    nodes: tuple[str, ...]
    edges: tuple[GlobalEdge, ...]
    length: int

    @property
    def found(self) -> bool:
        return self.length >= 0 and bool(self.nodes)


@dataclass(frozen=True, slots=True)
class ImpactReport:
    """Immutable impact analysis for one seed node."""

    seed: str
    affected: tuple[str, ...]
    depth: int
    relations: tuple[str, ...]


def find_region(graph: GlobalKnowledgeGraph, name_or_id: str) -> GlobalNode | None:
    """Find a Region node by id or name (case-insensitive name)."""

    key = name_or_id.strip().lower()
    for node in graph.nodes_of_type("Region"):
        if node.id.lower() == key or node.name.lower() == key:
            return node
    return None


def find_cluster(graph: GlobalKnowledgeGraph, name_or_id: str) -> GlobalNode | None:
    """Find a Cluster node by id or name."""

    key = name_or_id.strip().lower()
    for node in graph.nodes_of_type("Cluster"):
        if node.id.lower() == key or node.name.lower() == key:
            return node
    return None


def _adjacency(
    graph: GlobalKnowledgeGraph, *, reverse: bool = False
) -> dict[str, list[GlobalEdge]]:
    adj: dict[str, list[GlobalEdge]] = defaultdict(list)
    for edge in graph.edges:
        if reverse:
            adj[edge.target].append(edge)
        else:
            adj[edge.source].append(edge)
    return adj


def upstream(graph: GlobalKnowledgeGraph, node_id: str) -> tuple[GlobalNode, ...]:
    """Nodes that reach ``node_id`` (incoming BFS, one hop+)."""

    adj = _adjacency(graph, reverse=True)
    seen: set[str] = set()
    order: list[str] = []
    queue: deque[str] = deque([node_id])
    seen.add(node_id)
    while queue:
        cur = queue.popleft()
        for edge in adj.get(cur, ()):
            src = edge.source
            if src not in seen:
                seen.add(src)
                order.append(src)
                queue.append(src)
    nodes = graph.node_ids()
    return tuple(
        n for nid in order if (n := graph.get_node(nid)) is not None and nid in nodes
    )


def downstream(graph: GlobalKnowledgeGraph, node_id: str) -> tuple[GlobalNode, ...]:
    """Nodes reachable from ``node_id`` (outgoing BFS)."""

    adj = _adjacency(graph, reverse=False)
    seen: set[str] = set()
    order: list[str] = []
    queue: deque[str] = deque([node_id])
    seen.add(node_id)
    while queue:
        cur = queue.popleft()
        for edge in adj.get(cur, ()):
            dst = edge.target
            if dst not in seen:
                seen.add(dst)
                order.append(dst)
                queue.append(dst)
    return tuple(n for nid in order if (n := graph.get_node(nid)) is not None)


def shortest_path(graph: GlobalKnowledgeGraph, source: str, target: str) -> PathResult:
    """BFS shortest path by hop count; empty if unreachable."""

    if source == target:
        node = graph.get_node(source)
        if node is None:
            return PathResult(nodes=(), edges=(), length=-1)
        return PathResult(nodes=(source,), edges=(), length=0)

    adj = _adjacency(graph)
    prev: dict[str, tuple[str, GlobalEdge]] = {}
    queue: deque[str] = deque([source])
    seen = {source}
    found = False
    while queue:
        cur = queue.popleft()
        for edge in adj.get(cur, ()):
            nxt = edge.target
            if nxt in seen:
                continue
            seen.add(nxt)
            prev[nxt] = (cur, edge)
            if nxt == target:
                found = True
                queue.clear()
                break
            queue.append(nxt)
    if not found:
        return PathResult(nodes=(), edges=(), length=-1)

    nodes_rev: list[str] = [target]
    edges_rev: list[GlobalEdge] = []
    cur = target
    while cur != source:
        parent, edge = prev[cur]
        edges_rev.append(edge)
        nodes_rev.append(parent)
        cur = parent
    nodes_rev.reverse()
    edges_rev.reverse()
    return PathResult(
        nodes=tuple(nodes_rev), edges=tuple(edges_rev), length=len(edges_rev)
    )


def related_discoveries(
    graph: GlobalKnowledgeGraph, node_id: str
) -> tuple[GlobalNode, ...]:
    """Discovery nodes connected via VERIFIED_BY / CORRELATES / PREDICTS."""

    interesting = {"VERIFIED_BY", "CORRELATES", "PREDICTS", "CAUSES"}
    found: list[GlobalNode] = []
    seen: set[str] = set()
    for edge in graph.edges:
        if edge.relationship not in interesting:
            continue
        other: str | None = None
        if edge.source == node_id:
            other = edge.target
        elif edge.target == node_id:
            other = edge.source
        if other is None or other in seen:
            continue
        node = graph.get_node(other)
        if node is not None and node.type == "Discovery":
            seen.add(other)
            found.append(node)
    # Also discoveries reachable one hop from related cluster/region
    for node in downstream(graph, node_id):
        if node.type == "Discovery" and node.id not in seen:
            seen.add(node.id)
            found.append(node)
    return tuple(found)


def impact_analysis(
    graph: GlobalKnowledgeGraph, seed: str, *, max_depth: int = 4
) -> ImpactReport:
    """Downstream impact set from ``seed`` up to ``max_depth`` hops."""

    adj = _adjacency(graph)
    depth_map: dict[str, int] = {seed: 0}
    relations: set[str] = set()
    queue: deque[str] = deque([seed])
    while queue:
        cur = queue.popleft()
        if depth_map[cur] >= max_depth:
            continue
        for edge in adj.get(cur, ()):
            relations.add(edge.relationship)
            nxt = edge.target
            if nxt not in depth_map:
                depth_map[nxt] = depth_map[cur] + 1
                queue.append(nxt)
    affected = tuple(sorted(n for n in depth_map if n != seed))
    return ImpactReport(
        seed=seed,
        affected=affected,
        depth=max(depth_map.values()) if depth_map else 0,
        relations=tuple(sorted(relations)),
    )
