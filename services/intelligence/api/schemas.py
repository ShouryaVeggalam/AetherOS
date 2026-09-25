"""Pydantic request/response schemas for `/v9` GII endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CognitionCreateRequest(BaseModel):
    """POST /v9/cognition body."""

    goal: str = Field(min_length=1, description="Primary objective statement")
    context: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    workspace_id: str = Field(default="default", min_length=1)
    created_by: str = Field(default="system", min_length=1)


class CognitionPlanResponse(BaseModel):
    """Serialized cognition plan."""

    id: str
    workspace_id: str
    goal: str
    context: dict[str, Any]
    constraints: list[str]
    objectives: list[dict[str, Any]]
    complexity: dict[str, Any]
    allocation: dict[str, Any]
    execution_steps: list[str]
    confidence: float
    created_by: str
    created_at: str
    status: str


class CognitionListResponse(BaseModel):
    """List wrapper for cognition plans."""

    workspace_id: str
    count: int
    plans: list[CognitionPlanResponse]


class IntelligenceHealthResponse(BaseModel):
    """GET /v9/intelligence aggregate."""

    plan_count: int
    avg_confidence: float
    last_plan_at: str | None
    workspace_id: str
    modules_ready: list[str]
