"""Pydantic request/response schemas for Aether Lab OpenAPI surface."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AttentionSignalsIn(BaseModel):
    """Optional explicit attention signal overrides (0–1)."""

    task_complexity: float | None = Field(default=None, ge=0, le=1)
    available_context: float | None = Field(default=None, ge=0, le=1)
    memory_relevance: float | None = Field(default=None, ge=0, le=1)
    uncertainty: float | None = Field(default=None, ge=0, le=1)


class CognitionCreateRequest(BaseModel):
    """Create a goal, allocate attention, and draft a cognition plan."""

    objective: str = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    priority: float = Field(default=50.0, ge=0, le=100)
    context: dict[str, Any] = Field(default_factory=dict)
    signals: AttentionSignalsIn | None = None
    goal_id: str | None = None


class AttentionAllocateRequest(BaseModel):
    """Allocate attention for an existing or inline goal."""

    objective: str = Field(min_length=1)
    constraints: list[str] = Field(default_factory=list)
    priority: float = Field(default=50.0, ge=0, le=100)
    context: dict[str, Any] = Field(default_factory=dict)
    signals: AttentionSignalsIn | None = None
    goal_id: str | None = None


class AttentionSignalsOut(BaseModel):
    task_complexity: float
    available_context: float
    memory_relevance: float
    uncertainty: float


class AttentionAllocationResponse(BaseModel):
    id: str
    goal_id: str
    signals: AttentionSignalsOut
    weights: dict[str, float]
    reasoning_budget: float
    retrieval_budget: float
    factors: list[str]
    confidence: float
    created_at: datetime


class CognitionStageOut(BaseModel):
    name: str
    description: str
    attention_share: float


class CognitionPlanResponse(BaseModel):
    id: str
    goal_id: str
    complexity: Literal["trivial", "moderate", "complex", "strategic"]
    attention_budget: float
    stages: list[CognitionStageOut]
    confidence: float
    attention_id: str
    status: str
    created_at: datetime | None = None
    attention: AttentionAllocationResponse | None = None


class CognitionBundleResponse(BaseModel):
    """Cognition create response: goal + attention + draft plan."""

    goal_id: str
    objective: str
    attention: AttentionAllocationResponse
    plan: CognitionPlanResponse


class DecomposeRequest(BaseModel):
    objective: str = Field(min_length=1)
    plan_id: str | None = None
    max_depth: int = Field(default=3, ge=1, le=6)


class ReflectRequest(BaseModel):
    plan_id: str
    reasoning_summary: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)


class CritiqueRequest(BaseModel):
    plan_id: str
    reasoning_summary: str = Field(min_length=1)
    evidence: list[str] = Field(default_factory=list)


class ModulePendingResponse(BaseModel):
    """Placeholder for modules not yet shipped."""

    module: str
    status: Literal["pending"]
    message: str
    related_attention_id: str | None = None


class AetherHealthResponse(BaseModel):
    attention_count: int
    plan_count: int
    modules_ready: list[str]
    status: str
