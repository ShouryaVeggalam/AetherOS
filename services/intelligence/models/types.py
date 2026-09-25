"""Immutable GII domain types — Cognition Engine and health aggregates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

ComplexityTier = Literal["trivial", "moderate", "complex", "strategic"]
CognitionStatus = Literal["planned", "superseded"]


@dataclass(frozen=True, slots=True)
class CognitionRequest:
    """Inbound cognition brief.

    Attributes:
        goal: Primary objective statement (must be non-empty).
        context: Structured situational facts (read-only evidence).
        constraints: Hard limits the plan must respect.
        workspace_id: Tenant / venture scope.
        created_by: Operator or system actor id.
    """

    goal: str
    context: Mapping[str, Any]
    constraints: tuple[str, ...]
    workspace_id: str
    created_by: str


@dataclass(frozen=True, slots=True)
class ObjectiveNode:
    """One node in a recursive objective decomposition tree."""

    id: str
    statement: str
    parent_id: str | None
    depth: int
    priority: int


@dataclass(frozen=True, slots=True)
class ComplexityEstimate:
    """Complexity score derived from structure — not prediction."""

    score: float
    tier: ComplexityTier
    factors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ResourceAllocation:
    """Agents and knowledge domains required for the plan."""

    required_agents: tuple[str, ...]
    required_knowledge: tuple[str, ...]
    reasoning_budget: float


@dataclass(frozen=True, slots=True)
class CognitionPlan:
    """Immutable cognition plan — append-only historical record."""

    id: str
    workspace_id: str
    goal: str
    context: Mapping[str, Any]
    constraints: tuple[str, ...]
    objectives: tuple[ObjectiveNode, ...]
    complexity: ComplexityEstimate
    allocation: ResourceAllocation
    execution_steps: tuple[str, ...]
    confidence: float
    created_by: str
    created_at: datetime
    status: CognitionStatus = "planned"


@dataclass(frozen=True, slots=True)
class IntelligenceHealth:
    """Aggregate GII health derived from cognition history."""

    plan_count: int
    avg_confidence: float
    last_plan_at: datetime | None
    workspace_id: str
    modules_ready: tuple[str, ...] = field(default_factory=lambda: ("cognition",))
