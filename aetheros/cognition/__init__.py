"""AetherOS cognition — memory, causal graph, hypotheses, verify, plan.

Systems reasoning engine (not an LLM). Recommendation-only.
"""

from __future__ import annotations

from aetheros.cognition.causal_graph import (
    CausalGraph,
    CausalGraphBuilder,
    GraphEdge,
    GraphNode,
)
from aetheros.cognition.hypotheses import (
    Hypothesis,
    HypothesisSet,
    Observation,
    generate_hypotheses,
    observe_from_snapshot,
)
from aetheros.cognition.memory import CognitiveFact, CognitiveMemory
from aetheros.cognition.planner import CognitivePlanner, InterventionPlan, PlanSet
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
    verify_hypotheses,
)

__all__ = [
    "CausalGraph",
    "CausalGraphBuilder",
    "CognitiveFact",
    "CognitiveMemory",
    "CognitivePanel",
    "CognitivePlanner",
    "CognitiveReport",
    "CognitiveRuntime",
    "GraphEdge",
    "GraphNode",
    "Hypothesis",
    "HypothesisSet",
    "InterventionPlan",
    "Observation",
    "PlanSet",
    "VerificationResult",
    "VerifiedExplanation",
    "build_cognitive_report",
    "explain_reasoning",
    "generate_hypotheses",
    "observe_from_snapshot",
    "verify_hypotheses",
]
