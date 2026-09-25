"""Graph Intelligence Bridge — read-only ResourceGraph integration layer.

P5 architectural bridge. Existing prediction / explainability / simulation
engines are unchanged; they may optionally consume bridge outputs.
"""

from aetheros.bridge.adapter import GraphBridge
from aetheros.bridge.context import (
    ClusterSummary,
    GraphContext,
    GraphSnapshot,
    PredictionContext,
    ProcessResourceView,
    SimulationState,
    SnapshotDiff,
)
from aetheros.bridge.evidence import (
    edge_to_evidence,
    evidence_for_process,
    system_evidence,
)
from aetheros.bridge.explainability import (
    GraphReasoningPath,
    default_process_to_memory_path,
    evidence_chain,
    reasoning_chain_from_path,
    reasoning_path,
)
from aetheros.bridge.prediction import aggregate_percent, prediction_inputs
from aetheros.bridge.simulation import clone_graph, create_snapshot, diff_snapshots

__all__ = [
    "ClusterSummary",
    "GraphBridge",
    "GraphContext",
    "GraphReasoningPath",
    "GraphSnapshot",
    "PredictionContext",
    "ProcessResourceView",
    "SimulationState",
    "SnapshotDiff",
    "aggregate_percent",
    "clone_graph",
    "create_snapshot",
    "default_process_to_memory_path",
    "diff_snapshots",
    "edge_to_evidence",
    "evidence_chain",
    "evidence_for_process",
    "prediction_inputs",
    "reasoning_chain_from_path",
    "reasoning_path",
    "system_evidence",
]
