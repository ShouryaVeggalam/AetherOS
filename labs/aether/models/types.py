"""Immutable Aether cognitive domain types.

Frozen contracts for goals, plans, tasks, attention allocations, reflections,
and critiques. Deterministic and explainable — never opaque model logits.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

ComplexityTier = Literal["trivial", "moderate", "complex", "strategic"]
TaskType = Literal["strategic", "tactical", "operational", "execution"]
TaskStatus = Literal["pending", "ready", "active", "blocked", "done", "cancelled"]
PlanStatus = Literal["draft", "active", "revised", "archived"]
AttentionChannel = Literal["focus", "memory", "exploration", "verification"]


@dataclass(frozen=True, slots=True)
class Goal:
    """Executive objective that drives cognition.

    Attributes:
        id: Stable goal identifier.
        objective: Human-readable objective statement.
        constraints: Hard limits the plan must respect.
        priority: Relative priority in ``[0, 100]``.
        context: Structured situational evidence (read-only).
    """

    id: str
    objective: str
    constraints: tuple[str, ...]
    priority: float
    context: Mapping[str, Any]
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.objective.strip():
            raise ValueError("objective must be non-empty")
        if not 0.0 <= self.priority <= 100.0:
            raise ValueError("priority must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class AttentionSignals:
    """Normalized inputs to the Attention Engine (all in ``[0, 1]``)."""

    task_complexity: float
    available_context: float
    memory_relevance: float
    uncertainty: float

    def __post_init__(self) -> None:
        for name in (
            "task_complexity",
            "available_context",
            "memory_relevance",
            "uncertainty",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class AttentionAllocation:
    """Explainable attention decision produced by the Attention Engine."""

    id: str
    goal_id: str
    signals: AttentionSignals
    weights: Mapping[AttentionChannel, float]
    reasoning_budget: float
    retrieval_budget: float
    factors: tuple[str, ...]
    confidence: float
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.goal_id.strip():
            raise ValueError("goal_id must be non-empty")
        if not 0.0 <= self.reasoning_budget <= 1.0:
            raise ValueError("reasoning_budget must be in [0, 1]")
        if not 0.0 <= self.retrieval_budget <= 1.0:
            raise ValueError("retrieval_budget must be in [0, 1]")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        total = sum(float(self.weights[k]) for k in self.weights)
        if abs(total - 1.0) > 1e-6:
            raise ValueError("attention weights must sum to 1.0")


@dataclass(frozen=True, slots=True)
class CognitionStage:
    """One named stage in a hierarchical cognition plan."""

    name: str
    description: str
    attention_share: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        if not 0.0 <= self.attention_share <= 1.0:
            raise ValueError("attention_share must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class CognitionPlan:
    """Deterministic cognitive plan tying a goal to attention and stages."""

    id: str
    goal_id: str
    complexity: ComplexityTier
    attention_budget: float
    stages: tuple[CognitionStage, ...]
    confidence: float
    attention_id: str = ""
    status: PlanStatus = "draft"
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.goal_id.strip():
            raise ValueError("goal_id must be non-empty")
        if not 0.0 <= self.attention_budget <= 1.0:
            raise ValueError("attention_budget must be in [0, 1]")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class Task:
    """Node in a hierarchical DAG task graph."""

    id: str
    parent_task: str | None
    type: TaskType
    dependencies: tuple[str, ...]
    status: TaskStatus
    statement: str = ""
    depth: int = 0

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if self.depth < 0:
            raise ValueError("depth must be >= 0")


@dataclass(frozen=True, slots=True)
class Reflection:
    """Post-reasoning self-assessment used to revise plans."""

    reasoning_summary: str
    weaknesses: tuple[str, ...]
    assumptions: tuple[str, ...]
    improvements: tuple[str, ...]
    plan_id: str = ""
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.reasoning_summary.strip():
            raise ValueError("reasoning_summary must be non-empty")


@dataclass(frozen=True, slots=True)
class CritiqueScore:
    """Single critique criterion score in ``[0, 1]``."""

    criterion: Literal[
        "correctness",
        "completeness",
        "consistency",
        "evidence_quality",
        "confidence_calibration",
    ]
    score: float
    notes: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class Critique:
    """Machine-readable structured self-evaluation."""

    id: str
    plan_id: str
    scores: tuple[CritiqueScore, ...]
    overall: float
    verdict: Literal["pass", "revise", "reject"]
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not 0.0 <= self.overall <= 1.0:
            raise ValueError("overall must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class AetherHealth:
    """Observatory health aggregate for the Aether Lab runtime."""

    attention_count: int
    plan_count: int
    modules_ready: tuple[str, ...] = field(
        default_factory=lambda: ("attention",)
    )
    status: str = "ok"
