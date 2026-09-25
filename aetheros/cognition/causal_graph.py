"""Causal graph — directed systems relationships for cognition.

Nodes and edges are immutable. Graphs are rebuilt as snapshots, never
mutated in place during reasoning. No OS side effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aetheros.knowledge.resource_types import CausalRelationKind, ResourceKind


@dataclass(frozen=True, slots=True)
class GraphNode:
    """One node in the causal operating graph.

    Attributes:
        node_id: Stable id (e.g. resource:cpu, process:Cursor).
        kind: Resource / actor kind.
        label: Display label.
        attributes: Public numeric/string attrs (no private content).
    """

    node_id: str
    kind: ResourceKind
    label: str
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """Directed edge between two graph nodes.

    Attributes:
        source_id: From node.
        target_id: To node.
        relation: CausalRelationKind (CAUSES / USES / DEPENDS_ON / PREDICTS / EXPLAINS).
        weight: Strength 0.0–1.0.
        evidence: Short public justification.
    """

    source_id: str
    target_id: str
    relation: CausalRelationKind
    weight: float
    evidence: str

    def __post_init__(self) -> None:
        """Validate weight."""

        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("weight must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class CausalGraph:
    """Immutable snapshot of the cognitive causal graph."""

    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]

    def node(self, node_id: str) -> GraphNode | None:
        """Lookup a node by id."""

        for item in self.nodes:
            if item.node_id == node_id:
                return item
        return None

    def outgoing(self, node_id: str) -> tuple[GraphEdge, ...]:
        """Edges leaving a node."""

        return tuple(e for e in self.edges if e.source_id == node_id)

    def incoming(self, node_id: str) -> tuple[GraphEdge, ...]:
        """Edges entering a node."""

        return tuple(e for e in self.edges if e.target_id == node_id)

    def related(
        self,
        node_id: str,
        relation: CausalRelationKind | None = None,
    ) -> tuple[GraphEdge, ...]:
        """Outgoing edges optionally filtered by relation."""

        edges = self.outgoing(node_id)
        if relation is None:
            return edges
        return tuple(e for e in edges if e.relation == relation)


@dataclass
class CausalGraphBuilder:
    """Mutable builder that freezes into a CausalGraph snapshot."""

    _nodes: dict[str, GraphNode] = field(default_factory=dict, init=False)
    _edges: list[GraphEdge] = field(default_factory=list, init=False)

    def add_node(self, node: GraphNode) -> None:
        """Insert or replace a node."""

        self._nodes[node.node_id] = node

    def add_edge(self, edge: GraphEdge) -> None:
        """Append an edge (nodes should already exist)."""

        if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
            raise KeyError("edge endpoints must exist as nodes")
        self._edges.append(edge)

    def build(self) -> CausalGraph:
        """Freeze the current builder state into an immutable graph."""

        nodes = tuple(sorted(self._nodes.values(), key=lambda n: n.node_id))
        edges = tuple(self._edges)
        return CausalGraph(nodes=nodes, edges=edges)
