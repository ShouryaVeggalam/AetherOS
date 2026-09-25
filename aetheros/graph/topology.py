"""Infrastructure topology graph for Sentinel cascade analysis.

NetworkX-backed sample: node → cluster → datacenter → region,
plus service overlays. Distinct from Horizon planetary census.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from aetheros.graph.dependency import SEED_DEPENDENCIES, DependencyEdge
from aetheros.graph.services import SEED_SERVICES, ServiceNode


@dataclass(frozen=True, slots=True)
class InfraNode:
    """One immutable infrastructure entity."""

    node_id: str
    kind: str
    name: str
    capacity: float
    health: float


SEED_INFRA: tuple[InfraNode, ...] = (
    InfraNode("node.local.1", "node", "Local Node", 70.0, 0.97),
    InfraNode("cluster.local", "cluster", "Local Cluster", 80.0, 0.96),
    InfraNode("dc.local", "datacenter", "Local DC", 85.0, 0.98),
    InfraNode("region.local", "region", "Local Region", 90.0, 0.99),
    InfraNode("region.edge", "region", "Edge Region", 75.0, 0.94),
)


@dataclass
class DependencyGraph:
    """Mutable builder with immutable snapshot views."""

    _graph: nx.DiGraph = field(default_factory=nx.DiGraph, init=False, repr=False)
    _services: dict[str, ServiceNode] = field(
        default_factory=dict, init=False, repr=False
    )
    _infra: dict[str, InfraNode] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Load seeded services, infra, and dependencies."""

        for node in SEED_INFRA:
            self._infra[node.node_id] = node
            self._graph.add_node(
                node.node_id,
                kind=node.kind,
                name=node.name,
                capacity=node.capacity,
                health=node.health,
            )
        for svc in SEED_SERVICES:
            self._services[svc.service_id] = svc
            self._graph.add_node(
                svc.service_id,
                kind="service",
                name=svc.name,
                capacity=100.0 - svc.load,
                health=svc.health,
                tier=svc.tier,
            )
        for edge in SEED_DEPENDENCIES:
            self.add_dependency(edge)

    def add_dependency(self, edge: DependencyEdge) -> None:
        """Insert a dependency edge (endpoints must exist)."""

        if edge.source_id not in self._graph or edge.target_id not in self._graph:
            raise KeyError("both endpoints must exist")
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            kind=edge.kind,
            weight=edge.weight,
            note=edge.note,
        )

    def services(self) -> tuple[ServiceNode, ...]:
        """All service nodes."""

        return tuple(self._services.values())

    def infra(self) -> tuple[InfraNode, ...]:
        """All infrastructure nodes."""

        return tuple(self._infra.values())

    def neighbors(self, node_id: str) -> tuple[str, ...]:
        """Outbound dependency targets."""

        if node_id not in self._graph:
            return ()
        return tuple(str(n) for n in self._graph.successors(node_id))

    def reverse_dependents(self, node_id: str) -> tuple[str, ...]:
        """Inbound dependents (who requires this node)."""

        if node_id not in self._graph:
            return ()
        return tuple(str(n) for n in self._graph.predecessors(node_id))

    def cascade_order(self, origin: str, *, depth: int = 4) -> tuple[str, ...]:
        """BFS outward from ``origin`` along dependency edges."""

        if origin not in self._graph:
            return ()
        ordered: list[str] = []
        seen = {origin}
        frontier = [origin]
        level = 0
        while frontier and level < depth:
            nxt: list[str] = []
            for node in frontier:
                for succ in self._graph.successors(node):
                    sid = str(succ)
                    if sid not in seen:
                        seen.add(sid)
                        ordered.append(sid)
                        nxt.append(sid)
            frontier = nxt
            level += 1
        return tuple(ordered)

    def edge_weight(self, source: str, target: str) -> float:
        """Coupling weight or 0 if missing."""

        data = self._graph.get_edge_data(source, target)
        if not data:
            return 0.0
        return float(data.get("weight", 0.0))

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable graph summary."""

        return {
            "nodes": [
                {
                    "id": n,
                    "kind": d.get("kind"),
                    "name": d.get("name"),
                    "health": d.get("health"),
                }
                for n, d in self._graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": str(u),
                    "target": str(v),
                    "kind": d.get("kind"),
                    "weight": d.get("weight"),
                }
                for u, v, d in self._graph.edges(data=True)
            ],
        }
