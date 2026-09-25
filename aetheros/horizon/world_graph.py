"""World Graph — NetworkX-backed planetary knowledge graph.

Hierarchy: Earth → Region → Country → Datacenter → Cluster → Node → Process
plus edge / robotics / satellite / HPC overlays.

Read-only graph algorithms only. Never contacts live systems.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

import networkx as nx

from aetheros.horizon.topology import (
    DEFAULT_CENSUS,
    PlanetaryCensus,
    TopologyEdge,
    TopologyNode,
    build_sample_topology,
)


@dataclass
class WorldGraph:
    """Mutable builder wrapping an immutable snapshot API.

    The internal DiGraph is private; callers receive frozen views via
    ``snapshot`` / ``to_dict``.
    """

    census: PlanetaryCensus = field(default_factory=lambda: DEFAULT_CENSUS)
    _graph: nx.DiGraph = field(default_factory=nx.DiGraph, init=False, repr=False)
    _nodes: dict[str, TopologyNode] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        """Load the seeded sample topology."""

        nodes, edges = build_sample_topology()
        for node in nodes:
            self.add_node(node)
        for edge in edges:
            self.add_edge(edge)

    def add_node(self, node: TopologyNode) -> None:
        """Insert or replace one topology node."""

        self._nodes[node.node_id] = node
        self._graph.add_node(
            node.node_id,
            kind=node.kind,
            name=node.name,
            parent_id=node.parent_id,
            capacity_score=node.capacity_score,
            health=node.health,
        )

    def add_edge(self, edge: TopologyEdge) -> None:
        """Insert a directed relation (nodes must already exist)."""

        if edge.source_id not in self._graph or edge.target_id not in self._graph:
            raise KeyError("both endpoints must exist before adding an edge")
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            relation=edge.relation,
            weight=edge.weight,
        )

    def node(self, node_id: str) -> TopologyNode | None:
        """Lookup one node by id."""

        return self._nodes.get(node_id)

    def nodes(self) -> tuple[TopologyNode, ...]:
        """All topology nodes."""

        return tuple(self._nodes.values())

    def edges(self) -> tuple[TopologyEdge, ...]:
        """All topology edges."""

        result: list[TopologyEdge] = []
        for src, dst, data in self._graph.edges(data=True):
            result.append(
                TopologyEdge(
                    source_id=str(src),
                    target_id=str(dst),
                    relation=data.get("relation", "CONTAINS"),
                    weight=float(data.get("weight", 1.0)),
                )
            )
        return tuple(result)

    def children(self, node_id: str) -> tuple[TopologyNode, ...]:
        """Direct CONTAINS children of ``node_id``."""

        if node_id not in self._graph:
            return ()
        kids: list[TopologyNode] = []
        for _, dst, data in self._graph.out_edges(node_id, data=True):
            if data.get("relation") == "CONTAINS" and dst in self._nodes:
                kids.append(self._nodes[dst])
        return tuple(kids)

    def regions(self) -> tuple[TopologyNode, ...]:
        """Region-kind nodes."""

        return tuple(n for n in self._nodes.values() if n.kind == "region")

    def path(self, source: str, target: str) -> tuple[str, ...] | None:
        """Shortest containment/connect path, or None if disconnected."""

        try:
            return tuple(nx.shortest_path(self._graph, source, target))
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def subgraph_kinds(self, *kinds: str) -> nx.DiGraph:
        """Return a copy filtered to the given node kinds."""

        keep = {n.node_id for n in self._nodes.values() if n.kind in kinds}
        return self._graph.subgraph(keep).copy()

    def average_health(self, *, kind: str | None = None) -> float:
        """Mean health across nodes, optionally filtered by kind."""

        pool = [
            n.health for n in self._nodes.values() if kind is None or n.kind == kind
        ]
        if not pool:
            return 0.0
        return sum(pool) / len(pool)

    def iter_hierarchy(self, root: str = "earth") -> Iterator[tuple[int, TopologyNode]]:
        """Depth-first walk of CONTAINS edges from ``root``."""

        if root not in self._nodes:
            return
        stack: list[tuple[int, str]] = [(0, root)]
        seen: set[str] = set()
        while stack:
            depth, nid = stack.pop()
            if nid in seen:
                continue
            seen.add(nid)
            node = self._nodes[nid]
            yield depth, node
            for child in reversed(self.children(nid)):
                stack.append((depth + 1, child.node_id))

    def snapshot(self) -> WorldGraphSnapshot:
        """Freeze a read-only view for UI / API."""

        return WorldGraphSnapshot(
            census=self.census,
            node_count=len(self._nodes),
            edge_count=self._graph.number_of_edges(),
            sample_nodes=self.nodes(),
            sample_edges=self.edges(),
            region_health=tuple(
                (r.name, round(r.health * 100, 2)) for r in self.regions()
            ),
            world_health=self.census.world_health,
        )

    def to_dict(self) -> dict[str, Any]:
        """JSON-serializable graph summary."""

        snap = self.snapshot()
        return {
            "census": {
                "regions": snap.census.regions,
                "countries": snap.census.countries,
                "datacenters": snap.census.datacenters,
                "clusters": snap.census.clusters,
                "nodes": snap.census.nodes,
                "processes": snap.census.processes,
                "edge_devices": snap.census.edge_devices,
                "robots": snap.census.robots,
                "satellites": snap.census.satellites,
                "hpc_clusters": snap.census.hpc_clusters,
                "world_health": snap.census.world_health,
            },
            "sample": {
                "nodes": snap.node_count,
                "edges": snap.edge_count,
            },
            "region_health": [
                {"name": name, "health": health} for name, health in snap.region_health
            ],
            "nodes": [
                {
                    "id": n.node_id,
                    "kind": n.kind,
                    "name": n.name,
                    "parent_id": n.parent_id,
                    "health": n.health,
                    "capacity_score": n.capacity_score,
                }
                for n in snap.sample_nodes
            ],
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "relation": e.relation,
                    "weight": e.weight,
                }
                for e in snap.sample_edges
            ],
        }


@dataclass(frozen=True, slots=True)
class WorldGraphSnapshot:
    """Immutable world-graph view for dashboards and APIs."""

    census: PlanetaryCensus
    node_count: int
    edge_count: int
    sample_nodes: tuple[TopologyNode, ...]
    sample_edges: tuple[TopologyEdge, ...]
    region_health: tuple[tuple[str, float], ...]
    world_health: float
