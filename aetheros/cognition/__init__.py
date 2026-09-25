"""AetherOS cognition — legacy CognitiveRuntime + v3 Cognition Core.

Legacy path (unchanged): memory, causal graph, hypotheses, verifier, planner,
runtime — recommendation-only systems reasoning.

v3 Cognition Core (isolated): ``CognitionEngine`` converts graph evidence into
``CognitionState`` via observe → reason → verify → plan. Not an LLM.
"""

from __future__ import annotations

from aetheros.cognition.causal_graph import (
    CausalGraph,
    CausalGraphBuilder,
    GraphEdge,
    GraphNode,
)
from aetheros.cognition.engine import CognitionEngine
from aetheros.cognition.evidence import collect_evidence, context_label
from aetheros.cognition.formatter import CognitionCorePanel
from aetheros.cognition.hypotheses import (
    Hypothesis,
    HypothesisSet,
    Observation,
    generate_core_hypotheses,
    generate_hypotheses,
    observe_from_snapshot,
)
from aetheros.cognition.memory import (
    CognitiveFact,
    CognitiveMemory,
    OperationalMemory,
    OperationalPattern,
)
from aetheros.cognition.models import (
    CognitionPlan,
    CognitionState,
    Evidence,
    VerifiedCoreExplanation,
)
from aetheros.cognition.models import Hypothesis as CoreHypothesis
from aetheros.cognition.planner import (
    CognitivePlanner,
    InterventionPlan,
    PlanSet,
    generate_cognition_plans,
)
from aetheros.cognition.renderer import CognitivePanel
from aetheros.cognition.report import (
    CognitiveReport,
    build_cognitive_report,
    explain_reasoning,
)
from aetheros.cognition.runtime import CognitiveRuntime
from aetheros.cognition.verifier import (
    VerificationResult,
    VerifiedExplanation,
    verify_core_hypotheses,
    verify_hypotheses,
)

__all__ = [
    "CausalGraph",
    "CausalGraphBuilder",
    "CognitionCorePanel",
    "CognitionEngine",
    "CognitionPlan",
    "CognitionState",
    "CognitiveFact",
    "CognitiveMemory",
    "CognitivePanel",
    "CognitivePlanner",
    "CognitiveReport",
    "CognitiveRuntime",
    "CoreHypothesis",
    "Evidence",
    "GraphEdge",
    "GraphNode",
    "Hypothesis",
    "HypothesisSet",
    "InterventionPlan",
    "Observation",
    "OperationalMemory",
    "OperationalPattern",
    "PlanSet",
    "VerificationResult",
    "VerifiedCoreExplanation",
    "VerifiedExplanation",
    "build_cognitive_report",
    "collect_evidence",
    "context_label",
    "explain_reasoning",
    "generate_cognition_plans",
    "generate_core_hypotheses",
    "generate_hypotheses",
    "observe_from_snapshot",
    "verify_core_hypotheses",
    "verify_hypotheses",
]
