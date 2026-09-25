"""Causal Knowledge Graph models — verified relationships only.

Immutable contracts for the P3 intelligence layer. Distinct from the
Resource Graph (host topology) and from declarative OntologyConcept rows.
Never stores personal content or speculative links.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aetheros.knowledge.ontology import KnowledgeNodeType
from aetheros.knowledge.relationships import KnowledgeRelation


@dataclass(frozen=True, slots=True)
class KnowledgeNode:
    """One immutable node in the Causal Knowledge Graph.

    Attributes:
        id: Stable unique node id.
        type: Ontology node type (CPU, Memory, Discovery, …).
        name: Operator-facing label.
        metadata: Frozen key/value pairs (stringified).
        created_at: UTC timestamp when the node was materialised.
    """

    id: str
    type: KnowledgeNodeType
    name: str
    metadata: tuple[tuple[str, str], ...]
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("node id must be non-empty")
        if not self.name.strip():
            raise ValueError("node name must be non-empty")


@dataclass(frozen=True, slots=True)
class KnowledgeEdge:
    """One immutable directed verified relationship.

    Attributes:
        source: Source node id.
        target: Target node id.
        relationship: Typed causal / structural relation.
        confidence: Confidence 0–100.
        evidence_count: Supporting evidence units.
    """

    source: str
    target: str
    relationship: KnowledgeRelation
    confidence: float
    evidence_count: int

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.target.strip():
            raise ValueError("edge endpoints must be non-empty")
        if self.source == self.target:
            raise ValueError("self-loops are not allowed")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")
        if self.evidence_count < 1:
            raise ValueError("evidence_count must be >= 1")

    @property
    def key(self) -> tuple[str, str, str]:
        """Dedup key: source, target, relationship."""

        return (self.source, self.target, self.relationship)


@dataclass(frozen=True, slots=True)
class CausalKnowledgeGraph:
    """Immutable Causal Knowledge Graph snapshot.

    Attributes:
        nodes: All nodes.
        edges: All directed verified edges (no duplicates).
        schema_version: Serialization stamp.
    """

    nodes: tuple[KnowledgeNode, ...]
    edges: tuple[KnowledgeEdge, ...]
    schema_version: str = "1.0.0"

    def node_ids(self) -> frozenset[str]:
        """Return the set of node identifiers."""

        return frozenset(node.id for node in self.nodes)

    def get_node(self, node_id: str) -> KnowledgeNode | None:
        """Look up one node by id."""

        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def outgoing(self, node_id: str) -> tuple[KnowledgeEdge, ...]:
        """Edges leaving ``node_id``."""

        return tuple(e for e in self.edges if e.source == node_id)

    def incoming(self, node_id: str) -> tuple[KnowledgeEdge, ...]:
        """Edges entering ``node_id``."""

        return tuple(e for e in self.edges if e.target == node_id)
