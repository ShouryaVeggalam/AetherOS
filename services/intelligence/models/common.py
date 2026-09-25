"""Serialization helpers for GII domain objects."""

from __future__ import annotations

import uuid
from typing import Any

from services.intelligence.models.types import (
    CognitionPlan,
    ComplexityEstimate,
    IntelligenceHealth,
    ObjectiveNode,
    ResourceAllocation,
)


def new_id() -> str:
    """Return a new UUID4 string."""

    return str(uuid.uuid4())


def objective_to_dict(node: ObjectiveNode) -> dict[str, Any]:
    """Serialize an objective node."""

    return {
        "id": node.id,
        "statement": node.statement,
        "parent_id": node.parent_id,
        "depth": node.depth,
        "priority": node.priority,
    }


def complexity_to_dict(estimate: ComplexityEstimate) -> dict[str, Any]:
    """Serialize a complexity estimate."""

    return {
        "score": estimate.score,
        "tier": estimate.tier,
        "factors": list(estimate.factors),
    }


def allocation_to_dict(allocation: ResourceAllocation) -> dict[str, Any]:
    """Serialize a resource allocation."""

    return {
        "required_agents": list(allocation.required_agents),
        "required_knowledge": list(allocation.required_knowledge),
        "reasoning_budget": allocation.reasoning_budget,
    }


def plan_to_dict(plan: CognitionPlan) -> dict[str, Any]:
    """Serialize a cognition plan for OpenAPI / JSON responses."""

    return {
        "id": plan.id,
        "workspace_id": plan.workspace_id,
        "goal": plan.goal,
        "context": dict(plan.context),
        "constraints": list(plan.constraints),
        "objectives": [objective_to_dict(o) for o in plan.objectives],
        "complexity": complexity_to_dict(plan.complexity),
        "allocation": allocation_to_dict(plan.allocation),
        "execution_steps": list(plan.execution_steps),
        "confidence": plan.confidence,
        "created_by": plan.created_by,
        "created_at": plan.created_at.isoformat(),
        "status": plan.status,
    }


def health_to_dict(health: IntelligenceHealth) -> dict[str, Any]:
    """Serialize intelligence health."""

    return {
        "plan_count": health.plan_count,
        "avg_confidence": health.avg_confidence,
        "last_plan_at": (
            None if health.last_plan_at is None else health.last_plan_at.isoformat()
        ),
        "workspace_id": health.workspace_id,
        "modules_ready": list(health.modules_ready),
    }
