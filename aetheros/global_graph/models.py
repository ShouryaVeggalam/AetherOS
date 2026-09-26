"""Global Knowledge Graph models — immutable Horizon intelligence contracts.

v6.0 P3. Derived from verified snapshots and evidence only. Never stores
credentials or personal content. Distinct from CausalKnowledgeGraph.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from aetheros.global_graph.ontology import GlobalNodeType, is_global_node_type
from aetheros.global_graph.relationships import GlobalRelation, is_global_relation

GLOBAL_GRAPH_SCHEMA = "1.0.0"


@dataclass(frozen=True, slots=True)
class GlobalNode:
    """One immutable node in the Global Knowledge Graph."""

    id: str
    type: GlobalNodeType
    name: str
    created_at: datetime
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not is_global_node_type(str(self.type)):
            raise ValueError(f"invalid node type: {self.type!r}")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> GlobalNode:
        """Parse a GlobalNode from a mapping."""

        meta = data.get("metadata") or {}
        if not isinstance(meta, Mapping):
            raise ValueError("metadata must be a mapping")
        return cls(
            id=str(data.get("id") or "").strip(),
            type=str(data.get("type") or "").strip(),  # type: ignore[arg-type]
            name=str(data.get("name") or "").strip(),
            metadata=dict(meta),
            created_at=datetime.fromisoformat(str(data.get("created_at") or "")),
        )


@dataclass(frozen=True, slots=True)
class GlobalEdge:
    """One immutable directed verified relationship with evidence."""

    source: str
    target: str
    relationship: GlobalRelation
    confidence: float
    evidence_count: int
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.target.strip():
            raise ValueError("edge endpoints must be non-empty")
        if self.source == self.target:
            raise ValueError("self-loops are not allowed")
        if not is_global_relation(str(self.relationship)):
            raise ValueError(f"invalid relationship: {self.relationship!r}")
        if not 0.0 <= self.confidence <= 100.0:
            raise ValueError("confidence must be in [0, 100]")
        if self.evidence_count < 1:
            raise ValueError("evidence_count must be >= 1")
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))

    @property
    def key(self) -> tuple[str, str, str]:
        """Dedup key: source, target, relationship."""

        return (self.source, self.target, self.relationship)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "evidence_ids": list(self.evidence_ids),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> GlobalEdge:
        """Parse a GlobalEdge from a mapping."""

        evid = data.get("evidence_ids") or ()
        if isinstance(evid, str):
            evid = [evid]
        if not isinstance(evid, (list, tuple)):
            raise ValueError("evidence_ids must be a list")
        return cls(
            source=str(data.get("source") or "").strip(),
            target=str(data.get("target") or "").strip(),
            relationship=str(data.get("relationship") or "").strip(),  # type: ignore[arg-type]
            confidence=float(data.get("confidence") or 0.0),
            evidence_count=int(data.get("evidence_count") or 0),
            evidence_ids=tuple(str(x) for x in evid),
        )


@dataclass(frozen=True, slots=True)
class GlobalKnowledgeGraph:
    """Immutable Global Knowledge Graph snapshot for Horizon."""

    nodes: tuple[GlobalNode, ...]
    edges: tuple[GlobalEdge, ...]
    schema_version: str = GLOBAL_GRAPH_SCHEMA
    content_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "nodes", tuple(self.nodes))
        object.__setattr__(self, "edges", tuple(self.edges))

    def node_ids(self) -> frozenset[str]:
        """Set of node identifiers."""

        return frozenset(n.id for n in self.nodes)

    def get_node(self, node_id: str) -> GlobalNode | None:
        """Look up one node by id."""

        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def nodes_of_type(self, node_type: str) -> tuple[GlobalNode, ...]:
        """All nodes matching ``node_type``."""

        return tuple(n for n in self.nodes if n.type == node_type)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "schema_version": self.schema_version,
            "content_hash": self.content_hash,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> GlobalKnowledgeGraph:
        """Parse a GlobalKnowledgeGraph from a mapping."""

        nodes_raw = data.get("nodes") or ()
        edges_raw = data.get("edges") or ()
        if not isinstance(nodes_raw, (list, tuple)):
            raise ValueError("nodes must be a list")
        if not isinstance(edges_raw, (list, tuple)):
            raise ValueError("edges must be a list")
        return cls(
            nodes=tuple(GlobalNode.from_dict(n) for n in nodes_raw),
            edges=tuple(GlobalEdge.from_dict(e) for e in edges_raw),
            schema_version=str(data.get("schema_version") or GLOBAL_GRAPH_SCHEMA),
            content_hash=str(data.get("content_hash") or ""),
        )
