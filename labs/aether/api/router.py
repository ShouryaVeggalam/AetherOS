"""Aether Lab FastAPI routes under ``/aether``."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from labs.aether.api.schemas import (
    AetherHealthResponse,
    AttentionAllocateRequest,
    AttentionAllocationResponse,
    CognitionBundleResponse,
    CognitionCreateRequest,
    CognitionPlanResponse,
    CritiqueRequest,
    DecomposeRequest,
    ModulePendingResponse,
    ReflectRequest,
)
from labs.aether.api.serializers import allocation_to_response, plan_to_response
from labs.aether.runtime import get_aether_runtime

router = APIRouter(prefix="/aether", tags=["aether-lab"])


@router.get(
    "/health",
    response_model=AetherHealthResponse,
    summary="Aether Lab health",
)
async def aether_health() -> AetherHealthResponse:
    health = await get_aether_runtime().health()
    return AetherHealthResponse(
        attention_count=health.attention_count,
        plan_count=health.plan_count,
        modules_ready=list(health.modules_ready),
        status=health.status,
    )


@router.post(
    "/attention",
    response_model=AttentionAllocationResponse,
    summary="Allocate cognitive attention (Module 1)",
)
async def allocate_attention(
    body: AttentionAllocateRequest,
) -> AttentionAllocationResponse:
    """Run the Attention Engine for an objective."""

    rt = get_aether_runtime()
    overrides = _signal_overrides(body)
    try:
        _goal, allocation = await rt.attention.allocate_from_objective(
            body.objective,
            constraints=body.constraints,
            priority=body.priority,
            context=body.context,
            goal_id=body.goal_id,
            **overrides,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return allocation_to_response(allocation)


@router.get(
    "/attention/{allocation_id}",
    response_model=AttentionAllocationResponse,
    summary="Fetch an attention allocation",
)
async def get_attention(allocation_id: str) -> AttentionAllocationResponse:
    rt = get_aether_runtime()
    allocation = await rt.attention.get_allocation(allocation_id)
    if allocation is None:
        raise HTTPException(status_code=404, detail="attention allocation not found")
    return allocation_to_response(allocation)


@router.post(
    "/cognition",
    response_model=CognitionBundleResponse,
    summary="Create cognition plan (attention-backed draft)",
)
async def create_cognition(body: CognitionCreateRequest) -> CognitionBundleResponse:
    """Allocate attention and draft a cognition plan for an objective."""

    rt = get_aether_runtime()
    overrides = _signal_overrides(body)
    try:
        goal, allocation = await rt.attention.allocate_from_objective(
            body.objective,
            constraints=body.constraints,
            priority=body.priority,
            context=body.context,
            goal_id=body.goal_id,
            **overrides,
        )
        plan = await rt.attention.draft_plan(goal, allocation)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CognitionBundleResponse(
        goal_id=goal.id,
        objective=goal.objective,
        attention=allocation_to_response(allocation),
        plan=plan_to_response(plan, attention=allocation),
    )


@router.get(
    "/plans/{plan_id}",
    response_model=CognitionPlanResponse,
    summary="Fetch a cognition plan",
)
async def get_plan(plan_id: str) -> CognitionPlanResponse:
    rt = get_aether_runtime()
    plan = await rt.attention.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="cognition plan not found")
    attention = None
    if plan.attention_id:
        attention = await rt.attention.get_allocation(plan.attention_id)
    return plan_to_response(plan, attention=attention)


@router.post(
    "/decompose",
    response_model=ModulePendingResponse,
    summary="Decompose objective (Module — pending)",
)
async def decompose(body: DecomposeRequest) -> ModulePendingResponse:
    return ModulePendingResponse(
        module="decomposition",
        status="pending",
        message=(
            f"Decomposition Engine not yet shipped. "
            f"Objective recorded for Module 2+: {body.objective[:120]}"
        ),
    )


@router.post(
    "/reflect",
    response_model=ModulePendingResponse,
    summary="Reflect on reasoning (Module — pending)",
)
async def reflect(body: ReflectRequest) -> ModulePendingResponse:
    return ModulePendingResponse(
        module="reflection",
        status="pending",
        message=(
            f"Reflection Engine not yet shipped. "
            f"Plan {body.plan_id} summary length={len(body.reasoning_summary)}."
        ),
    )


@router.post(
    "/critique",
    response_model=ModulePendingResponse,
    summary="Critique reasoning (Module — pending)",
)
async def critique(body: CritiqueRequest) -> ModulePendingResponse:
    return ModulePendingResponse(
        module="critique",
        status="pending",
        message=(
            f"Critique Engine not yet shipped. "
            f"Plan {body.plan_id} awaiting Module N."
        ),
    )


def _signal_overrides(
    body: CognitionCreateRequest | AttentionAllocateRequest,
) -> dict[str, float | None]:
    if body.signals is None:
        return {
            "task_complexity": None,
            "available_context": None,
            "memory_relevance": None,
            "uncertainty": None,
        }
    return {
        "task_complexity": body.signals.task_complexity,
        "available_context": body.signals.available_context,
        "memory_relevance": body.signals.memory_relevance,
        "uncertainty": body.signals.uncertainty,
    }
