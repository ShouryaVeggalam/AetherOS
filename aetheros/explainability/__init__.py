"""AetherOS v1.2 — Explainable Intelligence Engine.

Evidence-based explanations for AI decisions. Never invents reasons.
"""

from __future__ import annotations

from aetheros.explainability.confidence import compute_confidence
from aetheros.explainability.evidence import EvidenceBundle, collect_evidence
from aetheros.explainability.formatter import ExplainabilityPanel, format_explanation
from aetheros.explainability.models import Evidence, Explanation, ReasoningChain
from aetheros.explainability.reasoning import (
    ExplainabilityEngine,
    build_reasoning_chain,
)

__all__ = [
    "Evidence",
    "EvidenceBundle",
    "ExplainabilityEngine",
    "ExplainabilityPanel",
    "Explanation",
    "ReasoningChain",
    "build_reasoning_chain",
    "collect_evidence",
    "compute_confidence",
    "format_explanation",
]
