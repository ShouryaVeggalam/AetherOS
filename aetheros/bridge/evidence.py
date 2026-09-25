"""Evidence bridge — convert ResourceGraph relationships into Evidence.

Never invents links. Every Evidence description is grounded in an existing
edge and its endpoint node names/metadata.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aetheros.explainability.models import Evidence
from aetheros.graph.models import ResourceEdge, ResourceGraph, ResourceNode
from aetheros.graph.queries import edges_from, get_process_resources, nodes_of_type


def system_evidence(
    graph: ResourceGraph,
    *,
    now: datetime | None = None,
    limit: int = 64,
) -> tuple[Evidence, ...]:
    """Materialise graph-backed Evidence for process→resource relationships.

    Args:
        graph: Immutable resource graph.
        now: Optional clock override for deterministic tests.
        limit: Maximum evidence items (keeps payloads bounded).

    Returns:
        Immutable Evidence tuple with ``source="graph"``.
    """

    stamp = now if now is not None else datetime.now(UTC)
    items: list[Evidence] = []
    for process in nodes_of_type(graph, "Process"):
        for edge in get_process_resources(graph, process.id):
            target = graph.get_node(edge.target)
            if target is None:
                continue
            items.append(_edge_evidence(process, edge, target, stamp))
            if len(items) >= limit:
                return tuple(items)
    if not items:
        for edge in graph.edges:
            source = graph.get_node(edge.source)
            target = graph.get_node(edge.target)
            if source is None or target is None:
                continue
            items.append(_edge_evidence(source, edge, target, stamp))
            if len(items) >= limit:
                break
    return tuple(items)


def evidence_for_process(
    graph: ResourceGraph,
    process_id: str,
    *,
    now: datetime | None = None,
) -> tuple[Evidence, ...]:
    """Evidence for one process node's outbound resource edges."""

    stamp = now if now is not None else datetime.now(UTC)
    process = graph.get_node(process_id)
    if process is None or process.type != "Process":
        return ()
    items: list[Evidence] = []
    for edge in edges_from(graph, process_id):
        target = graph.get_node(edge.target)
        if target is None:
            continue
        items.append(_edge_evidence(process, edge, target, stamp))
    return tuple(items)


def edge_to_evidence(
    source: ResourceNode,
    edge: ResourceEdge,
    target: ResourceNode,
    stamp: datetime,
) -> Evidence:
    """Build one Evidence fact from a typed edge (public helper)."""

    return _edge_evidence(source, edge, target, stamp)


def _edge_evidence(
    source: ResourceNode,
    edge: ResourceEdge,
    target: ResourceNode,
    stamp: datetime,
) -> Evidence:
    """Build one Evidence fact from a typed edge."""

    metric = _metric_for(target)
    value = _meta_float(target, "percent")
    if edge.relationship == "USES":
        description = f"{source.name} currently depends on {target.name}"
    elif edge.relationship == "ALLOCATES":
        description = f"{source.name} currently allocates {target.name}"
    elif edge.relationship == "DEPENDS_ON":
        description = f"{source.name} currently depends on {target.name}"
    else:
        relation = edge.relationship.replace("_", " ").lower()
        description = f"{source.name} {relation} {target.name}"
    return Evidence(
        source="graph",
        metric=metric,
        value=value,
        timestamp=stamp,
        description=description,
    )


def _metric_for(node: ResourceNode) -> str:
    """Map node type to a stable metric key."""

    mapping = {
        "CPU": "cpu_usage",
        "Memory": "memory_usage",
        "Disk": "disk_usage",
        "GPU": "gpu_usage",
        "Battery": "battery_level",
        "Network": "network_usage",
    }
    return mapping.get(node.type, f"{node.type.lower()}_link")


def _meta_float(node: ResourceNode, key: str) -> float:
    """Parse a metadata float or return 0.0."""

    for meta_key, value in node.metadata:
        if meta_key == key:
            try:
                return float(value)
            except ValueError:
                return 0.0
    return 0.0
