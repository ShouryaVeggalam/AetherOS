"""Causal inference over ResourceGraph edges (graph reasoning extension).

Preserves cognitive ``CausalGraph`` helpers above. Resource-graph causal
chains are derived only from existing typed edges — never fabricated.
"""

from __future__ import annotations

from aetheros.cognition.causal_graph import CausalGraph, GraphEdge
from aetheros.graph.models import ResourceGraph
from aetheros.graph.queries import nodes_of_type
from aetheros.knowledge.resource_types import CausalRelationKind
from aetheros.reasoning.models import ReasoningPath
from aetheros.reasoning.traversal import (
    DEFAULT_RELATIONS,
    find_all_paths,
    find_shortest_path,
)

# ---------------------------------------------------------------------------
# Cognitive CausalGraph helpers (unchanged public API)
# ---------------------------------------------------------------------------


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
    relation: CausalRelationKind | None = None,
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


# ---------------------------------------------------------------------------
# Resource Graph causal chains (P6)
# ---------------------------------------------------------------------------

CAUSAL_EDGE_TYPES: frozenset[str] = frozenset(
    {
        "USES",
        "ALLOCATES",
        "DEPENDS_ON",
        "COMMUNICATES",
        "SIMULATES",
        "PREDICTS",
    }
)


def infer_causal_chain(
    graph: ResourceGraph,
    source_id: str,
    target_id: str,
) -> ReasoningPath | None:
    """Shortest causal chain between two nodes using allowed edge types.

    Returns:
        ``ReasoningPath`` or ``None`` when no real edge path exists.
    """

    return find_shortest_path(
        graph,
        source_id,
        target_id,
        relations=CAUSAL_EDGE_TYPES,
    )


def causal_chains_from(
    graph: ResourceGraph,
    source_id: str,
    *,
    target_types: frozenset[str] | None = None,
    limit: int = 8,
) -> tuple[ReasoningPath, ...]:
    """All causal paths from ``source_id`` to matching target node types."""

    types = target_types or frozenset({"CPU", "Memory", "Disk", "GPU", "Battery"})
    chains: list[ReasoningPath] = []
    for node in graph.nodes:
        if node.id == source_id or node.type not in types:
            continue
        for path in find_all_paths(
            graph,
            source_id,
            node.id,
            relations=CAUSAL_EDGE_TYPES,
            max_depth=6,
            limit=4,
        ):
            chains.append(path)
            if len(chains) >= limit:
                return tuple(chains)
    return tuple(chains)


def primary_process_resource_chain(
    graph: ResourceGraph,
) -> ReasoningPath | None:
    """First process → deepest resource chain (CPU→Memory→Disk preference)."""

    processes = nodes_of_type(graph, "Process")
    if not processes:
        return None
    process = processes[0]
    preferred_targets = ("disk", "memory", "cpu")
    for target_id in preferred_targets:
        resolved = target_id
        if graph.get_node(resolved) is None:
            if target_id != "disk":
                continue  # pragma: no cover
            disks = nodes_of_type(graph, "Disk")
            if not disks:
                continue  # pragma: no cover
            resolved = disks[0].id
        chain = infer_causal_chain(graph, process.id, resolved)
        if chain is not None and chain.depth > 0:
            return chain
    for node in graph.nodes:  # pragma: no cover
        if node.type not in {"CPU", "Memory", "Disk"}:
            continue
        chain = infer_causal_chain(graph, process.id, node.id)
        if chain is not None and chain.depth > 0:
            return chain
    return None  # pragma: no cover


def format_chain_labels(path: ReasoningPath) -> str:
    """Render ``A → B → C`` from path node names."""

    return " → ".join(node.name for node in path.nodes)


assert CAUSAL_EDGE_TYPES <= DEFAULT_RELATIONS
