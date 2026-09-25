"""Resource Graph query engine — pure reads over immutable graphs.

All helpers return new immutable tuples/objects. No graph mutation.
"""

from __future__ import annotations

from aetheros.graph.models import ResourceEdge, ResourceGraph, ResourceNode


def get_neighbors(
    graph: ResourceGraph,
    node_id: str,
    *,
    direction: str = "out",
) -> tuple[ResourceNode, ...]:
    """Return neighboring nodes.

    Args:
        graph: Resource graph.
        node_id: Anchor node id.
        direction: ``out`` (successors), ``in`` (predecessors), or ``both``.
    """

    ids: set[str] = set()
    if direction in {"out", "both"}:
        ids.update(edge.target for edge in graph.edges if edge.source == node_id)
    if direction in {"in", "both"}:
        ids.update(edge.source for edge in graph.edges if edge.target == node_id)
    return tuple(node for node in graph.nodes if node.id in ids)


def get_dependents(graph: ResourceGraph, node_id: str) -> tuple[ResourceNode, ...]:
    """Return nodes with DEPENDS_ON or USES edges pointing at ``node_id``."""

    dependent_ids = {
        edge.source
        for edge in graph.edges
        if edge.target == node_id and edge.relationship in {"DEPENDS_ON", "USES"}
    }
    return tuple(node for node in graph.nodes if node.id in dependent_ids)


def find_path(
    graph: ResourceGraph,
    source: str,
    target: str,
) -> tuple[str, ...] | None:
    """BFS shortest path of node ids, or ``None`` if unreachable."""

    if source not in graph.node_ids() or target not in graph.node_ids():
        return None
    if source == target:
        return (source,)
    adjacency: dict[str, list[str]] = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        adjacency.setdefault(edge.source, []).append(edge.target)
    queue: list[str] = [source]
    parents: dict[str, str | None] = {source: None}
    while queue:
        current = queue.pop(0)
        for nxt in adjacency.get(current, ()):
            if nxt in parents:
                continue
            parents[nxt] = current
            if nxt == target:
                return _reconstruct(parents, target)
            queue.append(nxt)
    return None


def subgraph(
    graph: ResourceGraph,
    node_ids: frozenset[str] | set[str],
) -> ResourceGraph:
    """Return an immutable subgraph induced by ``node_ids``."""

    keep = frozenset(node_ids)
    nodes = tuple(node for node in graph.nodes if node.id in keep)
    edges = tuple(
        edge
        for edge in graph.edges
        if edge.source in keep and edge.target in keep
    )
    return ResourceGraph(
        nodes=nodes,
        edges=edges,
        schema_version=graph.schema_version,
    )


def get_process_resources(
    graph: ResourceGraph,
    process_id: str,
) -> tuple[ResourceEdge, ...]:
    """Return outbound resource edges from one process node."""

    node = graph.get_node(process_id)
    if node is None or node.type != "Process":
        return ()
    return tuple(edge for edge in graph.edges if edge.source == process_id)


def edges_from(graph: ResourceGraph, node_id: str) -> tuple[ResourceEdge, ...]:
    """Return all outbound edges from ``node_id``."""

    return tuple(edge for edge in graph.edges if edge.source == node_id)


def nodes_of_type(graph: ResourceGraph, node_type: str) -> tuple[ResourceNode, ...]:
    """Return all nodes matching ``node_type``."""

    return tuple(node for node in graph.nodes if node.type == node_type)


def _reconstruct(
    parents: dict[str, str | None],
    target: str,
) -> tuple[str, ...]:
    """Rebuild a path from BFS parent pointers."""

    path: list[str] = []
    current: str | None = target
    while current is not None:
        path.append(current)
        current = parents[current]
    path.reverse()
    return tuple(path)
