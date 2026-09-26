"""Read-only Resource Graph & Context facades for plugins.

Hosts inject frozen snapshots. Plugins cannot mutate graph structure,
telemetry stores, or context engines.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class GraphNodeView:
    """Immutable view of one resource-graph node."""

    id: str
    name: str
    kind: str
    attributes: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class GraphEdgeView:
    """Immutable view of one resource-graph edge."""

    source: str
    target: str
    relation: str
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class GraphSnapshot:
    """Frozen Resource Graph projection for plugin consumption."""

    nodes: tuple[GraphNodeView, ...] = ()
    edges: tuple[GraphEdgeView, ...] = ()

    def node_ids(self) -> tuple[str, ...]:
        return tuple(n.id for n in self.nodes)

    def nodes_of_kind(self, kind: str) -> tuple[GraphNodeView, ...]:
        key = kind.strip().lower()
        return tuple(n for n in self.nodes if n.kind.lower() == key)


@dataclass(frozen=True, slots=True)
class ContextSnapshot:
    """Frozen situational context projection (non-personal keys only)."""

    intent: str = ""
    labels: tuple[tuple[str, str], ...] = ()
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "labels": dict(self.labels),
            "notes": list(self.notes),
        }


@dataclass
class GraphAPI:
    """Read-only Resource Graph access for plugins."""

    _snapshot: GraphSnapshot = field(default_factory=GraphSnapshot)

    def set_snapshot(self, snapshot: GraphSnapshot) -> None:
        """Host-only: publish a new immutable graph snapshot."""

        self._snapshot = snapshot

    def snapshot(self) -> GraphSnapshot:
        """Return the current frozen graph snapshot."""

        return self._snapshot

    def get_node(self, node_id: str) -> GraphNodeView | None:
        """Lookup one node by id."""

        for node in self._snapshot.nodes:
            if node.id == node_id:
                return node
        return None

    def list_nodes(self) -> tuple[GraphNodeView, ...]:
        return self._snapshot.nodes

    def list_edges(self) -> tuple[GraphEdgeView, ...]:
        return self._snapshot.edges


@dataclass
class ContextAPI:
    """Read-only Context access for plugins."""

    _snapshot: ContextSnapshot = field(default_factory=ContextSnapshot)

    def set_snapshot(self, snapshot: ContextSnapshot) -> None:
        """Host-only: publish a new immutable context snapshot."""

        self._snapshot = snapshot

    def snapshot(self) -> ContextSnapshot:
        return self._snapshot

    def intent(self) -> str:
        return self._snapshot.intent

    def label(self, key: str, default: str = "") -> str:
        mapping = dict(self._snapshot.labels)
        return str(mapping.get(key, default))


def graph_from_mapping(data: Mapping[str, Any]) -> GraphSnapshot:
    """Build a ``GraphSnapshot`` from a plain mapping (tests / adapters)."""

    nodes_raw: Sequence[Any] = data.get("nodes") or ()
    edges_raw: Sequence[Any] = data.get("edges") or ()
    nodes: list[GraphNodeView] = []
    for item in nodes_raw:
        attrs = item.get("attributes") or {}
        if isinstance(attrs, Mapping):
            attr_tuples = tuple((str(k), str(v)) for k, v in attrs.items())
        else:
            attr_tuples = tuple(attrs)
        nodes.append(
            GraphNodeView(
                id=str(item.get("id", "")),
                name=str(item.get("name", "")),
                kind=str(item.get("kind", "Unknown")),
                attributes=attr_tuples,
            )
        )
    edges = tuple(
        GraphEdgeView(
            source=str(item.get("source", "")),
            target=str(item.get("target", "")),
            relation=str(item.get("relation", "RELATED")),
            weight=float(item.get("weight", 1.0)),
        )
        for item in edges_raw
    )
    return GraphSnapshot(nodes=tuple(n for n in nodes if n.id), edges=edges)
