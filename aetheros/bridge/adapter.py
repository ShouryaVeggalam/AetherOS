"""GraphBridge adapter — unified read-only facade over ResourceGraph.

Subsystems should consume bridge outputs instead of walking telemetry
structures. The underlying ResourceGraph is never mutated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from aetheros.bridge.context import (
    ClusterSummary,
    GraphContext,
    GraphSnapshot,
    PredictionContext,
    ProcessResourceView,
    SimulationState,
    SnapshotDiff,
)
from aetheros.bridge.evidence import evidence_for_process, system_evidence
from aetheros.bridge.explainability import (
    GraphReasoningPath,
)
from aetheros.bridge.explainability import (
    evidence_chain as build_evidence_chain,
)
from aetheros.bridge.explainability import (
    reasoning_path as build_reasoning_path,
)
from aetheros.bridge.prediction import prediction_inputs
from aetheros.bridge.simulation import (
    clone_graph as clone_resource_graph,
)
from aetheros.bridge.simulation import (
    create_snapshot as take_snapshot,
)
from aetheros.bridge.simulation import (
    diff_snapshots as diff_graph_snapshots,
)
from aetheros.explainability.models import Evidence
from aetheros.graph.models import ResourceGraph, ResourceNode
from aetheros.graph.queries import get_neighbors, get_process_resources, nodes_of_type


@dataclass(frozen=True, slots=True)
class GraphBridge:
    """Immutable facade over one ResourceGraph snapshot.

    Attributes:
        graph: Canonical host resource graph (read-only).
        historical_window: Declared prediction history window (samples).
    """

    graph: ResourceGraph
    historical_window: int = 60

    def current_context(self, *, now: datetime | None = None) -> GraphContext:
        """Build the shared GraphContext from graph nodes only."""

        stamp = now if now is not None else datetime.now(UTC)
        intent = self.active_intent()
        processes = nodes_of_type(self.graph, "Process")
        foreground = processes[0].name if processes else None
        battery = self.graph.get_node("battery")
        battery_state = None
        if battery is not None:
            battery_state = _meta(battery, "percent")
        cluster = self.get_cluster_summary()
        sim = self.simulation_state()
        return GraphContext(
            active_intent=intent,
            foreground_process=foreground,
            cluster_health=cluster.health,
            battery_state=battery_state,
            simulation_active=sim.active,
            timestamp=stamp,
        )

    def get_process_resources(self, pid: int | str) -> ProcessResourceView | None:
        """Return outbound resource edges for a process id or node id."""

        process_id = (
            pid
            if isinstance(pid, str) and pid.startswith("process:")
            else f"process:{pid}"
        )
        node = self.graph.get_node(process_id)
        if node is None or node.type != "Process":
            # Allow bare numeric lookup already handled; also try rank-style ids.
            for candidate in nodes_of_type(self.graph, "Process"):
                if candidate.id == str(pid) or candidate.name == str(pid):
                    node = candidate
                    process_id = candidate.id
                    break
            else:
                return None
        edges = get_process_resources(self.graph, process_id)
        targets = tuple(
            target
            for edge in edges
            if (target := self.graph.get_node(edge.target)) is not None
        )
        return ProcessResourceView(
            process_id=process_id,
            process_name=node.name,
            edges=edges,
            targets=targets,
        )

    def get_cluster_summary(self) -> ClusterSummary:
        """Summarise Cluster-typed nodes (empty → unknown health)."""

        nodes = nodes_of_type(self.graph, "Cluster")
        if not nodes:
            return ClusterSummary(node_count=0, health="unknown", node_ids=())
        ids = tuple(node.id for node in nodes)
        return ClusterSummary(node_count=len(nodes), health="present", node_ids=ids)

    def get_resource_neighbors(
        self,
        node_id: str,
        *,
        direction: str = "out",
    ) -> tuple[ResourceNode, ...]:
        """Delegate to graph query ``get_neighbors`` (immutable)."""

        return get_neighbors(self.graph, node_id, direction=direction)

    def active_intent(self) -> str | None:
        """Return the active intent name when an Intent node exists."""

        node = self.graph.get_node("intent:active")
        return node.name if node is not None else None

    def simulation_state(self) -> SimulationState:
        """Report Simulation-typed nodes without inventing activity."""

        nodes = nodes_of_type(self.graph, "Simulation")
        return SimulationState(active=bool(nodes), simulation_nodes=nodes)

    def system_evidence(self, *, now: datetime | None = None) -> tuple[Evidence, ...]:
        """Graph-sourced Evidence for the whole host graph."""

        return system_evidence(self.graph, now=now)

    def prediction_inputs(self) -> PredictionContext:
        """PredictionContext for ForecastEngine adapters."""

        return prediction_inputs(
            self.graph,
            historical_window=self.historical_window,
        )

    def reasoning_path(
        self,
        source_id: str,
        target_id: str,
        *,
        now: datetime | None = None,
    ) -> GraphReasoningPath | None:
        """Verified graph path for explainability (or None)."""

        return build_reasoning_path(self.graph, source_id, target_id, now=now)

    def evidence_chain(
        self,
        *,
        process_id: str | None = None,
        now: datetime | None = None,
    ) -> tuple[Evidence, ...]:
        """Ordered evidence chain for a process or the system."""

        return build_evidence_chain(self.graph, process_id=process_id, now=now)

    def process_evidence(
        self, process_id: str, *, now: datetime | None = None
    ) -> tuple[Evidence, ...]:
        """Evidence limited to one process node's outbound edges."""

        return evidence_for_process(self.graph, process_id, now=now)

    def create_snapshot(self, *, now: datetime | None = None) -> GraphSnapshot:
        """Immutable topology snapshot for twin sandboxes."""

        return take_snapshot(self.graph, now=now)

    def clone_graph(self) -> ResourceGraph:
        """Structural clone of the underlying ResourceGraph."""

        return clone_resource_graph(self.graph)

    def diff_snapshots(
        self, before: GraphSnapshot, after: GraphSnapshot
    ) -> SnapshotDiff:
        """Diff two snapshots (pure set arithmetic)."""

        return diff_graph_snapshots(before, after)


def _meta(node: ResourceNode, key: str) -> str | None:
    """Read one metadata value or None."""

    for meta_key, value in node.metadata:
        if meta_key == key:
            return value
    return None
