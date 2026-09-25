"""Fabric universal graph — devices, clusters, agents, knowledge.

NetworkX-backed sample covering personal/server/cloud/edge/robot/IoT/AI.
Never contacts live infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import networkx as nx

from aetheros.fabric.identity import SEED_IDENTITIES

FabricNodeKind = Literal[
    "device",
    "cluster",
    "datacenter",
    "gpu",
    "storage",
    "network",
    "ai_agent",
    "simulation",
    "knowledge",
    "region",
]

FabricRelation = Literal[
    "CONNECTS",
    "HOSTS",
    "DEPENDS_ON",
    "SYNCHRONIZES",
    "PREDICTS",
    "EXPLAINS",
]


@dataclass(frozen=True, slots=True)
class FabricNode:
    """One immutable entity in the universal fabric graph."""

    node_id: str
    kind: FabricNodeKind
    name: str
    health: float
    metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate health."""

        if not 0.0 <= self.health <= 1.0:
            raise ValueError("health must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class FabricEdge:
    """One immutable fabric relation."""

    source_id: str
    target_id: str
    relation: FabricRelation
    weight: float = 1.0


@dataclass
class FabricGraph:
    """Universal fabric graph builder with snapshot views."""

    _graph: nx.DiGraph = field(default_factory=nx.DiGraph, init=False, repr=False)
    _nodes: dict[str, FabricNode] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Seed a compact universal sample."""

        seeds: list[FabricNode] = [
            FabricNode("region.local", "region", "Local Region", 0.99),
            FabricNode("region.cloud", "region", "Cloud Region", 0.98),
            FabricNode("region.edge", "region", "Edge Region", 0.96),
            FabricNode("dc.local", "datacenter", "Local DC", 0.98),
            FabricNode("dc.cloud", "datacenter", "Cloud DC", 0.97),
            FabricNode("cluster.local", "cluster", "Local Cluster", 0.97),
            FabricNode("cluster.gpu", "cluster", "GPU Cluster", 0.95),
            FabricNode("gpu.pool.1", "gpu", "GPU Pool", 0.94),
            FabricNode("storage.obj.1", "storage", "Object Store", 0.99),
            FabricNode("net.backbone", "network", "Backbone", 0.98),
            FabricNode("agent.coordinator", "ai_agent", "Coordinator Agent", 0.99),
            FabricNode("sim.global", "simulation", "Global Twin", 1.0),
            FabricNode("knowledge.genesis", "knowledge", "Genesis KB", 0.99),
        ]
        for identity in SEED_IDENTITIES:
            seeds.append(
                FabricNode(
                    identity.node_id,
                    "device",
                    identity.display_name,
                    0.97,
                    (("class", identity.node_class), ("region", identity.region_id)),
                )
            )
        for node in seeds:
            self.add_node(node)

        edges: list[FabricEdge] = [
            FabricEdge("region.local", "dc.local", "HOSTS", 1.0),
            FabricEdge("region.cloud", "dc.cloud", "HOSTS", 1.0),
            FabricEdge("dc.local", "cluster.local", "HOSTS", 1.0),
            FabricEdge("dc.cloud", "cluster.gpu", "HOSTS", 1.0),
            FabricEdge("cluster.gpu", "gpu.pool.1", "HOSTS", 1.0),
            FabricEdge("cluster.local", "storage.obj.1", "HOSTS", 0.8),
            FabricEdge("net.backbone", "region.local", "CONNECTS", 0.9),
            FabricEdge("net.backbone", "region.cloud", "CONNECTS", 0.9),
            FabricEdge("net.backbone", "region.edge", "CONNECTS", 0.85),
            FabricEdge("node.local.pc", "cluster.local", "DEPENDS_ON", 0.7),
            FabricEdge("node.cloud.gpu.1", "gpu.pool.1", "DEPENDS_ON", 0.95),
            FabricEdge("node.edge.1", "region.edge", "CONNECTS", 0.8),
            FabricEdge("node.local.pc", "node.server.1", "SYNCHRONIZES", 0.75),
            FabricEdge("node.server.1", "node.cloud.gpu.1", "SYNCHRONIZES", 0.7),
            FabricEdge("agent.coordinator", "sim.global", "PREDICTS", 0.6),
            FabricEdge("knowledge.genesis", "agent.coordinator", "EXPLAINS", 0.65),
            FabricEdge("sim.global", "region.cloud", "PREDICTS", 0.55),
        ]
        for edge in edges:
            self.add_edge(edge)

    def add_node(self, node: FabricNode) -> None:
        """Insert or replace a fabric node."""

        self._nodes[node.node_id] = node
        self._graph.add_node(
            node.node_id,
            kind=node.kind,
            name=node.name,
            health=node.health,
        )

    def add_edge(self, edge: FabricEdge) -> None:
        """Insert a relation (endpoints must exist)."""

        if edge.source_id not in self._graph or edge.target_id not in self._graph:
            raise KeyError("both endpoints must exist")
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            relation=edge.relation,
            weight=edge.weight,
        )

    def nodes(self) -> tuple[FabricNode, ...]:
        """All fabric nodes."""

        return tuple(self._nodes.values())

    def edges(self) -> tuple[FabricEdge, ...]:
        """All fabric edges."""

        result: list[FabricEdge] = []
        for src, dst, data in self._graph.edges(data=True):
            result.append(
                FabricEdge(
                    str(src),
                    str(dst),
                    data.get("relation", "CONNECTS"),
                    float(data.get("weight", 1.0)),
                )
            )
        return tuple(result)

    def average_health(self) -> float:
        """Mean node health."""

        values = [n.health for n in self._nodes.values()]
        if not values:
            return 0.0
        return sum(values) / len(values)

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable graph summary."""

        return {
            "nodes": [
                {
                    "id": n.node_id,
                    "kind": n.kind,
                    "name": n.name,
                    "health": n.health,
                }
                for n in self.nodes()
            ],
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "relation": e.relation,
                    "weight": e.weight,
                }
                for e in self.edges()
            ],
        }
