"""AetherOS reasoning layer — abductive, deductive, causal, explain.

Pure inference helpers over cognition outputs. No OS side effects.
"""

from __future__ import annotations

from aetheros.reasoning.abductive import abduct
from aetheros.reasoning.causal import causes_of, explainers_of, trace_path
from aetheros.reasoning.deductive import DeductiveConclusion, deduce
from aetheros.reasoning.explain import (
    CognitiveReport,
    build_cognitive_report,
    explain_reasoning,
)

__all__ = [
    "CognitiveReport",
    "DeductiveConclusion",
    "abduct",
    "build_cognitive_report",
    "causes_of",
    "deduce",
    "explain_reasoning",
    "explainers_of",
    "trace_path",
]
