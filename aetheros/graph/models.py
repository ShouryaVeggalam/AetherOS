"""Resource Graph models — immutable host intelligence graph contracts.

Canonical directed graph types for prediction, reasoning, explainability,
and simulation. Distinct from Sentinel ``DependencyGraph`` (service cascade).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

NodeType = Literal[
    "CPU",
    "Memory",
    "Disk",
    "GPU",
    "Network",
    "Process",
    "Battery",
    "Intent",
    "Cluster",
    "Simulation",
    "Research",
]

EdgeRelation = Literal[
    "USES",
    "ALLOCATES",
    "DEPENDS_ON",
    "COMMUNICATES",
    "SIMULATES",
    "PREDICTS",
]

NODE_TYPES: frozenset[str] = frozenset(
    {
        "CPU",
        "Memory",
        "Disk",
        "GPU",
        "Network",
        "Process",
        "Battery",
        "Intent",
        "Cluster",
        "Simulation",
        "Research",
    }
)

EDGE_RELATIONS: frozenset[str] = frozenset(
    {
        "USES",
        "ALLOCATES",
        "DEPENDS_ON",
        "COMMUNICATES",
        "SIMULATES",
        "PREDICTS",
    }
)

RESOURCE_GRAPH_SCHEMA = "1.0.0"


@dataclass(frozen=True, slots=True)
class ResourceNode:
    """One immutable resource / actor node in the host graph.

    Attributes:
        id: Stable unique node id (e.g. ``cpu``, ``process:1234``).
        type: Canonical node type.
        name: Operator-facing label.
        metadata: Frozen key/value pairs (stringified measurements).
        created_at: UTC timestamp when the node was materialised.
    """

    id: str
    type: NodeType
    name: str
    metadata: tuple[tuple[str, str], ...]
    created_at: datetime

    def __post_init__(self) -> None:
        """Reject empty identifiers."""

        if not self.id.strip():
            raise ValueError("node id must be non-empty")
        if not self.name.strip():
            raise ValueError("node name must be non-empty")


@dataclass(frozen=True, slots=True)
class ResourceEdge:
    """One immutable directed relationship between resource nodes.

    Attributes:
        source: Source node id.
        target: Target node id.
        relationship: Typed edge relation.
        weight: Strength in [0, 1].
    """

    source: str
    target: str
    relationship: EdgeRelation
    weight: float

    def __post_init__(self) -> None:
        """Validate endpoints and weight bounds."""

        if not self.source.strip() or not self.target.strip():
            raise ValueError("edge endpoints must be non-empty")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("edge weight must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class ResourceGraph:
    """Immutable directed resource graph snapshot.

    Attributes:
        nodes: All nodes in the graph.
        edges: All directed edges.
        schema_version: Serialization schema stamp.
    """

    nodes: tuple[ResourceNode, ...]
    edges: tuple[ResourceEdge, ...]
    schema_version: str = RESOURCE_GRAPH_SCHEMA

    def node_ids(self) -> frozenset[str]:
        """Return the set of node identifiers."""

        return frozenset(node.id for node in self.nodes)

    def get_node(self, node_id: str) -> ResourceNode | None:
        """Look up one node by id."""

        for node in self.nodes:
            if node.id == node_id:
                return node
        return None
