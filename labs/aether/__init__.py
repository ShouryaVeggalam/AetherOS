"""Aether Lab — Cognitive Architecture of CELESTRA X.

Foundation models perform inference. Aether performs cognition:
attention → decomposition → planning → reasoning → reflection → critique → decision.

Module 1 (shipped): Attention Engine.
"""

from __future__ import annotations

from labs.aether.attention import (
    AttentionEngine,
    allocate_attention,
    derive_signals,
)
from labs.aether.models import (
    AttentionAllocation,
    AttentionSignals,
    CognitionPlan,
    Goal,
    Reflection,
    Task,
)
from labs.aether.observatory import build_attention_map, render_attention_ascii
from labs.aether.runtime import AetherRuntime, get_aether_runtime, reset_aether_runtime

__all__ = [
    "AetherRuntime",
    "AttentionAllocation",
    "AttentionEngine",
    "AttentionSignals",
    "CognitionPlan",
    "Goal",
    "Reflection",
    "Task",
    "allocate_attention",
    "build_attention_map",
    "derive_signals",
    "get_aether_runtime",
    "render_attention_ascii",
    "reset_aether_runtime",
]

__version__ = "0.1.0"
