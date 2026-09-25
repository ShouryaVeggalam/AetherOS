"""AetherOS reasoning layer — cognitive helpers + Graph Reasoning Engine.

* Cognitive: abductive / deductive / CausalGraph trace (pre-P6).
* Graph Reasoning Engine (v2.0 P6): ResourceGraph causal paths & verification.
"""

from __future__ import annotations

from aetheros.reasoning.abductive import abduct
from aetheros.reasoning.causal import (
    CAUSAL_EDGE_TYPES,
    causal_chains_from,
    causes_of,
    explainers_of,
    format_chain_labels,
    infer_causal_chain,
    primary_process_resource_chain,
    trace_path,
)
from aetheros.reasoning.confidence import compute_confidence
from aetheros.reasoning.deductive import DeductiveConclusion, deduce
from aetheros.reasoning.explain import (
    CognitiveReport,
    build_cognitive_report,
    explain_reasoning,
)
from aetheros.reasoning.formatter import GraphReasoningPanel
from aetheros.reasoning.hypotheses import generate_hypotheses
from aetheros.reasoning.models import (
    Hypothesis,
    Observation,
    ReasoningPath,
    VerifiedExplanation,
)
from aetheros.reasoning.traversal import (
    common_dependencies,
    dependents,
    find_all_paths,
    find_shortest_path,
    neighbors,
)
from aetheros.reasoning.verifier import (
    observation_from_metrics,
    reason,
    verify_hypotheses,
)

__all__ = [
    "CAUSAL_EDGE_TYPES",
    "CognitiveReport",
    "DeductiveConclusion",
    "GraphReasoningPanel",
    "Hypothesis",
    "Observation",
    "ReasoningPath",
    "VerifiedExplanation",
    "abduct",
    "build_cognitive_report",
    "causal_chains_from",
    "causes_of",
    "common_dependencies",
    "compute_confidence",
    "deduce",
    "dependents",
    "explain_reasoning",
    "explainers_of",
    "find_all_paths",
    "find_shortest_path",
    "format_chain_labels",
    "generate_hypotheses",
    "infer_causal_chain",
    "neighbors",
    "observation_from_metrics",
    "primary_process_resource_chain",
    "reason",
    "trace_path",
    "verify_hypotheses",
]
