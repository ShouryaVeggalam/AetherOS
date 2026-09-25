"""Simulation bridge — immutable ResourceGraph snapshots for digital twins.

Never mutates graphs. Never invokes SimulationEngine or TwinSimulator.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aetheros.bridge.context import GraphSnapshot, SnapshotDiff
from aetheros.graph.models import ResourceEdge, ResourceGraph, ResourceNode


def create_snapshot(
    graph: ResourceGraph,
    *,
    now: datetime | None = None,
) -> GraphSnapshot:
    """Capture topology keys for one immutable graph."""

    stamp = now if now is not None else datetime.now(UTC)
    return GraphSnapshot(
        graph_schema=graph.schema_version,
        node_ids=graph.node_ids(),
        edge_keys=frozenset(_edge_key(edge) for edge in graph.edges),
        node_count=len(graph.nodes),
        edge_count=len(graph.edges),
        created_at=stamp,
    )


def clone_graph(graph: ResourceGraph) -> ResourceGraph:
    """Return a new ResourceGraph with copied node/edge tuples.

    Because models are frozen, this is a structural copy of the containers —
    useful for twin sandboxes that must not share identity with the live graph.
    """

    nodes = tuple(
        ResourceNode(
            id=node.id,
            type=node.type,
            name=node.name,
            metadata=tuple(node.metadata),
            created_at=node.created_at,
        )
        for node in graph.nodes
    )
    edges = tuple(
        ResourceEdge(
            source=edge.source,
            target=edge.target,
            relationship=edge.relationship,
            weight=edge.weight,
        )
        for edge in graph.edges
    )
    return ResourceGraph(
        nodes=nodes,
        edges=edges,
        schema_version=graph.schema_version,
    )


def diff_snapshots(before: GraphSnapshot, after: GraphSnapshot) -> SnapshotDiff:
    """Set-difference of node ids and edge keys between two snapshots."""

    return SnapshotDiff(
        added_nodes=after.node_ids - before.node_ids,
        removed_nodes=before.node_ids - after.node_ids,
        added_edges=after.edge_keys - before.edge_keys,
        removed_edges=before.edge_keys - after.edge_keys,
    )


def _edge_key(edge: ResourceEdge) -> str:
    """Stable identity for an edge in snapshot diffs."""

    return f"{edge.source}->{edge.target}:{edge.relationship}"
