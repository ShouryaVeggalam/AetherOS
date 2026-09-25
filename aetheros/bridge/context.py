"""Graph Intelligence Bridge context models — shared immutable contracts.

Cross-subsystem read models derived only from a ResourceGraph. No I/O,
no mutation, no telemetry traversal.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from aetheros.graph.models import ResourceEdge, ResourceNode


@dataclass(frozen=True, slots=True)
class ClusterSummary:
    """Immutable cluster view extracted from Cluster-typed graph nodes."""

    node_count: int
    health: str
    node_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProcessResourceView:
    """Immutable process → resource edge projection."""

    process_id: str
    process_name: str
    edges: tuple[ResourceEdge, ...]
    targets: tuple[ResourceNode, ...]


@dataclass(frozen=True, slots=True)
class GraphContext:
    """Operator-facing host context shared across every intelligence subsystem.

    Attributes:
        active_intent: Active intent profile name, or None.
        foreground_process: Highest-ranked process name, or None.
        cluster_health: Aggregate cluster health label.
        battery_state: Battery percent string, or None when absent.
        simulation_active: True when a Simulation node exists in the graph.
        timestamp: Context materialisation time (UTC).
    """

    active_intent: str | None
    foreground_process: str | None
    cluster_health: str
    battery_state: str | None
    simulation_active: bool
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class PredictionContext:
    """Read-only prediction inputs derived from the Resource Graph.

    The ForecastEngine itself is unchanged; callers may feed aggregates from
    these node sets instead of walking raw telemetry structures.

    Attributes:
        cpu_nodes: CPU-typed nodes (package + cores).
        memory_nodes: Memory-typed nodes.
        gpu_nodes: GPU-typed nodes (empty unless telemetry supplied them).
        active_processes: Process-typed nodes.
        intent: Active intent name, or None.
        historical_window: Declared sample window size (caller-supplied).
    """

    cpu_nodes: tuple[ResourceNode, ...]
    memory_nodes: tuple[ResourceNode, ...]
    gpu_nodes: tuple[ResourceNode, ...]
    active_processes: tuple[ResourceNode, ...]
    intent: str | None
    historical_window: int


@dataclass(frozen=True, slots=True)
class SimulationState:
    """Whether the graph currently encodes an active simulation node."""

    active: bool
    simulation_nodes: tuple[ResourceNode, ...]


@dataclass(frozen=True, slots=True)
class GraphSnapshot:
    """Immutable point-in-time copy of a ResourceGraph plus stamp."""

    graph_schema: str
    node_ids: frozenset[str]
    edge_keys: frozenset[str]
    node_count: int
    edge_count: int
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SnapshotDiff:
    """Immutable set difference between two GraphSnapshots."""

    added_nodes: frozenset[str]
    removed_nodes: frozenset[str]
    added_edges: frozenset[str]
    removed_edges: frozenset[str]

    @property
    def empty(self) -> bool:
        """True when the snapshots describe identical topology keys."""

        return not (
            self.added_nodes
            or self.removed_nodes
            or self.added_edges
            or self.removed_edges
        )
