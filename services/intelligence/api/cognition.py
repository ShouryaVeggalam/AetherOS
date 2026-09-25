"""/v9 Cognition Engine routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from services.intelligence.api.schemas import (
    CognitionCreateRequest,
    CognitionListResponse,
    CognitionPlanResponse,
    IntelligenceHealthResponse,
)
from services.intelligence.models.common import health_to_dict, plan_to_dict
from services.intelligence.runtime import get_intelligence_runtime

router = APIRouter(tags=["gii-cognition"])


@router.post(
    "/cognition",
    response_model=CognitionPlanResponse,
    summary="Create a cognition plan",
)
async def create_cognition(body: CognitionCreateRequest) -> CognitionPlanResponse:
    """Understand a goal and return an immutable cognition plan."""

    rt = get_intelligence_runtime()
    try:
        plan = await rt.cognition.understand(
            body.goal,
            body.context,
            body.constraints,
            workspace_id=body.workspace_id,
            created_by=body.created_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CognitionPlanResponse(**plan_to_dict(plan))


@router.get(
    "/cognition/{plan_id}",
    response_model=CognitionPlanResponse,
    summary="Fetch a cognition plan",
)
async def get_cognition(plan_id: str) -> CognitionPlanResponse:
    """Return a previously stored cognition plan."""

    rt = get_intelligence_runtime()
    plan = await rt.cognition.get(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="cognition plan not found")
    return CognitionPlanResponse(**plan_to_dict(plan))


@router.get(
    "/cognition",
    response_model=CognitionListResponse,
    summary="List cognition plans",
)
async def list_cognition(
    workspace_id: str = Query(default="default"),
    limit: int = Query(default=50, ge=1, le=500),
) -> CognitionListResponse:
    """List cognition plans for a workspace (newest first)."""

    rt = get_intelligence_runtime()
    plans = await rt.cognition.list(workspace_id=workspace_id, limit=limit)
    serialized = [CognitionPlanResponse(**plan_to_dict(p)) for p in plans]
    return CognitionListResponse(
        workspace_id=workspace_id,
        count=len(serialized),
        plans=serialized,
    )


@router.get(
    "/intelligence",
    response_model=IntelligenceHealthResponse,
    summary="Intelligence health",
)
async def intelligence_health(
    workspace_id: str = Query(default="default"),
) -> IntelligenceHealthResponse:
    """Aggregate GII health for a workspace from cognition history."""

    rt = get_intelligence_runtime()
    health = await rt.cognition.health(workspace_id=workspace_id)
    return IntelligenceHealthResponse(**health_to_dict(health))
