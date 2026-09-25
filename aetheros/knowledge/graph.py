"""Causal Knowledge Graph container helpers — read-only facade.

Wraps ``CausalKnowledgeGraph`` with adjacency indexes. Never mutates
input graphs; all derived views are new immutable tuples.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime

from aetheros.knowledge.models import (
    CausalKnowledgeGraph,
    KnowledgeEdge,
    KnowledgeNode,
)


@dataclass(frozen=True, slots=True)
class KnowledgeGraphView:
    """Indexed read-only view over a Causal Knowledge Graph snapshot."""

    graph: CausalKnowledgeGraph
    _out: dict[str, tuple[KnowledgeEdge, ...]]
    _in: dict[str, tuple[KnowledgeEdge, ...]]
    _nodes: dict[str, KnowledgeNode]

    @classmethod
    def from_graph(cls, graph: CausalKnowledgeGraph) -> KnowledgeGraphView:
        """Build adjacency indexes without mutating ``graph``."""

        out: dict[str, list[KnowledgeEdge]] = defaultdict(list)
        inn: dict[str, list[KnowledgeEdge]] = defaultdict(list)
        nodes = {n.id: n for n in graph.nodes}
        for edge in graph.edges:
            out[edge.source].append(edge)
            inn[edge.target].append(edge)
        return cls(
            graph=graph,
            _out={k: tuple(v) for k, v in out.items()},
            _in={k: tuple(v) for k, v in inn.items()},
            _nodes=nodes,
        )

    def get(self, node_id: str) -> KnowledgeNode | None:
        """Look up a node by id."""

        return self._nodes.get(node_id)

    def outgoing(self, node_id: str) -> tuple[KnowledgeEdge, ...]:
        """Indexed outgoing edges."""

        return self._out.get(node_id, ())

    def incoming(self, node_id: str) -> tuple[KnowledgeEdge, ...]:
        """Indexed incoming edges."""

        return self._in.get(node_id, ())

    def nodes_by_type(self, node_type: str) -> tuple[KnowledgeNode, ...]:
        """Return nodes matching an ontology type."""

        return tuple(n for n in self.graph.nodes if n.type == node_type)

    def edge_count(self) -> int:
        return len(self.graph.edges)

    def node_count(self) -> int:
        return len(self.graph.nodes)


def empty_graph(*, schema_version: str = "1.0.0") -> CausalKnowledgeGraph:
    """Return an empty immutable Causal Knowledge Graph."""

    return CausalKnowledgeGraph(nodes=(), edges=(), schema_version=schema_version)


def stamp_now() -> datetime:
    """UTC timestamp helper for builders / tests."""

    return datetime.now(UTC)
