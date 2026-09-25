"""Aether Lab — Cognitive Architecture of CELESTRA X.

Foundation models perform inference. Aether performs cognition:
attention → decomposition → planning → reasoning → reflection → critique → decision.

Modules shipped: Attention, Decomposition, Planning, Reflection, Critique.
"""

from __future__ import annotations

from labs.aether.attention import (
    AttentionEngine,
    allocate_attention,
    derive_signals,
)
from labs.aether.cognition import CognitionBundle, CognitionEngine
from labs.aether.critique import CritiqueEngine, critique_reasoning
from labs.aether.decomposition import (
    DecompositionEngine,
    decompose_objective,
    topological_order,
)
from labs.aether.models import (
    AttentionAllocation,
    AttentionSignals,
    CognitionPlan,
    Critique,
    Goal,
    Reflection,
    Task,
    TaskGraph,
)
from labs.aether.observatory import (
    build_attention_map,
    build_task_graph_view,
    render_attention_ascii,
    render_task_graph_ascii,
)
from labs.aether.planning import PlanningEngine, build_plan_from_graph, revise_plan
from labs.aether.reflection import ReflectionEngine, reflect_on_reasoning
from labs.aether.runtime import AetherRuntime, get_aether_runtime, reset_aether_runtime

__all__ = [
    "AetherRuntime",
    "AttentionAllocation",
    "AttentionEngine",
    "AttentionSignals",
    "CognitionBundle",
    "CognitionEngine",
    "CognitionPlan",
    "Critique",
    "CritiqueEngine",
    "DecompositionEngine",
    "Goal",
    "PlanningEngine",
    "Reflection",
    "ReflectionEngine",
    "Task",
    "TaskGraph",
    "allocate_attention",
    "build_attention_map",
    "build_plan_from_graph",
    "build_task_graph_view",
    "critique_reasoning",
    "decompose_objective",
    "derive_signals",
    "get_aether_runtime",
    "reflect_on_reasoning",
    "render_attention_ascii",
    "render_task_graph_ascii",
    "reset_aether_runtime",
    "revise_plan",
    "topological_order",
]

__version__ = "0.2.0"
