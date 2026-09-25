"""Signal normalization for the Attention Engine.

Converts raw cognitive cues into bounded ``AttentionSignals`` so allocation
is deterministic and comparable across goals.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from labs.aether.models.types import AttentionSignals, Goal

# Keyword evidence for complexity / uncertainty / memory cues.
_COMPLEXITY_CUES: tuple[str, ...] = (
    "complex",
    "multi-step",
    "hierarchical",
    "strategic",
    "decompose",
    "architecture",
    "system",
    "trade-off",
    "tradeoff",
)
_UNCERTAINTY_CUES: tuple[str, ...] = (
    "uncertain",
    "unknown",
    "ambiguous",
    "unclear",
    "hypothesis",
    "speculate",
    "maybe",
    "risk",
)
_MEMORY_CUES: tuple[str, ...] = (
    "memory",
    "prior",
    "history",
    "recall",
    "evidence",
    "known",
    "precedent",
    "pattern",
)


def derive_signals(
    goal: Goal,
    *,
    task_complexity: float | None = None,
    available_context: float | None = None,
    memory_relevance: float | None = None,
    uncertainty: float | None = None,
) -> AttentionSignals:
    """Derive normalized attention signals from a goal and optional overrides.

    Explicit overrides win. Otherwise signals are estimated from objective
    text, constraints, priority, and context keys — never invented beyond
    evidence in those fields.
    """

    corpus = _corpus(goal)
    complexity = (
        _clamp(task_complexity)
        if task_complexity is not None
        else _estimate_complexity(goal, corpus)
    )
    context_avail = (
        _clamp(available_context)
        if available_context is not None
        else _estimate_context(goal)
    )
    memory = (
        _clamp(memory_relevance)
        if memory_relevance is not None
        else _estimate_memory(goal, corpus)
    )
    uncertain = (
        _clamp(uncertainty)
        if uncertainty is not None
        else _estimate_uncertainty(goal, corpus)
    )
    return AttentionSignals(
        task_complexity=complexity,
        available_context=context_avail,
        memory_relevance=memory,
        uncertainty=uncertain,
    )


def _corpus(goal: Goal) -> str:
    parts: list[str] = [goal.objective, *goal.constraints]
    for key, value in goal.context.items():
        parts.append(str(key))
        if isinstance(value, (str, int, float)):
            parts.append(str(value))
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            parts.extend(str(v) for v in value)
    return " ".join(parts).lower()


def _estimate_complexity(goal: Goal, corpus: str) -> float:
    cue_hits = sum(1 for cue in _COMPLEXITY_CUES if cue in corpus)
    constraint_boost = min(0.35, 0.07 * len(goal.constraints))
    priority_boost = (goal.priority / 100.0) * 0.2
    length_boost = min(0.25, max(0.0, (len(goal.objective.split()) - 6) * 0.02))
    raw = 0.15 + 0.1 * cue_hits + constraint_boost + priority_boost + length_boost
    return round(_clamp(raw), 4)


def _estimate_context(goal: Goal) -> float:
    keys = len(goal.context)
    if keys == 0:
        return 0.15
    # Non-empty values count as usable context evidence.
    filled = 0
    for value in goal.context.values():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, (list, tuple, dict)) and len(value) == 0:
            continue
        filled += 1
    raw = 0.2 + 0.15 * min(5, filled) + 0.05 * min(4, keys)
    return round(_clamp(raw), 4)


def _estimate_memory(goal: Goal, corpus: str) -> float:
    cue_hits = sum(1 for cue in _MEMORY_CUES if cue in corpus)
    ctx = goal.context
    explicit = 0.0
    for key in ("memory_relevance", "memory", "evidence_score"):
        if key in ctx:
            try:
                explicit = max(explicit, float(ctx[key]))  # type: ignore[arg-type]
            except (TypeError, ValueError):
                continue
    if explicit > 1.0:
        explicit = explicit / 100.0
    raw = max(0.1 + 0.12 * cue_hits, _clamp(explicit) if explicit else 0.0)
    return round(_clamp(raw), 4)


def _estimate_uncertainty(goal: Goal, corpus: str) -> float:
    cue_hits = sum(1 for cue in _UNCERTAINTY_CUES if cue in corpus)
    sparse_context = 0.25 if len(goal.context) == 0 else 0.0
    raw = 0.12 + 0.14 * cue_hits + sparse_context
    # High priority with sparse evidence raises uncertainty.
    if goal.priority >= 70.0 and len(goal.context) < 2:
        raw += 0.1
    return round(_clamp(raw), 4)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def signals_from_mapping(data: Mapping[str, Any]) -> AttentionSignals:
    """Build signals from a raw mapping (API / tests)."""

    return AttentionSignals(
        task_complexity=_clamp(float(data.get("task_complexity", 0.5))),
        available_context=_clamp(float(data.get("available_context", 0.5))),
        memory_relevance=_clamp(float(data.get("memory_relevance", 0.5))),
        uncertainty=_clamp(float(data.get("uncertainty", 0.5))),
    )
