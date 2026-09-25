"""Cognitive explainability — compatibility re-exports.

``CognitiveReport`` and narrative helpers live in
``aetheros.cognition.report`` (owning package). This module re-exports
them so ``from aetheros.reasoning.explain import …`` keeps working.
"""

from __future__ import annotations

from aetheros.cognition.report import (
    CognitiveReport,
    build_cognitive_report,
    explain_reasoning,
)

__all__ = [
    "CognitiveReport",
    "build_cognitive_report",
    "explain_reasoning",
]
