"""Aether Lab FastAPI routes under ``/aether``."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from labs.aether.api.schemas import (
    AetherHealthResponse,
    AttentionAllocateRequest,
    AttentionAllocationResponse,
    CognitionBundleResponse,
    CognitionCreateRequest,
    CognitionPlanResponse,
    CritiqueRequest,
    CritiqueResponse,
    DecomposeRequest,
    ReflectRequest,
    ReflectionResponse,
    TaskGraphResponse,
)
from labs.aether.api.serializers import (
    allocation_to_response,
    critique_to_response,
    graph_to_response,
    plan_to_response,
    reflection_to_response,
)
from labs.aether.models.types import Goal
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
        task_graph_count=health.task_graph_count,
        reflection_count=health.reflection_count,
        critique_count=health.critique_count,
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
    summary="Run cognition pipeline (attention → decompose → plan)",
)
async def create_cognition(body: CognitionCreateRequest) -> CognitionBundleResponse:
    """Full Module 1–2 cognition: allocate, decompose, hierarchical plan."""

    rt = get_aether_runtime()
    overrides = _signal_overrides(body)
    try:
        bundle = await rt.cognition.run(
            body.objective,
            constraints=body.constraints,
            priority=body.priority,
            context=body.context,
            goal_id=body.goal_id,
            max_depth=body.max_depth,
            **overrides,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CognitionBundleResponse(
        goal_id=bundle.goal.id,
        objective=bundle.goal.objective,
        attention=allocation_to_response(bundle.attention),
        task_graph=graph_to_response(bundle.task_graph),
        plan=plan_to_response(bundle.plan, attention=bundle.attention),
    )


@router.get(
    "/plans/{plan_id}",
    response_model=CognitionPlanResponse,
    summary="Fetch a cognition plan",
)
async def get_plan(plan_id: str) -> CognitionPlanResponse:
    rt = get_aether_runtime()
    plan = await rt.planning.get(plan_id)
    if plan is None:
        plan = await rt.attention.get_plan(plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="cognition plan not found")
    attention = None
    if plan.attention_id:
        attention = await rt.attention.get_allocation(plan.attention_id)
    return plan_to_response(plan, attention=attention)


@router.post(
    "/decompose",
    response_model=TaskGraphResponse,
    summary="Decompose objective into hierarchical DAG (Module 2)",
)
async def decompose(body: DecomposeRequest) -> TaskGraphResponse:
    rt = get_aether_runtime()
    stamp = datetime.now(UTC)
    goal = Goal(
        id=body.goal_id or f"goal_{uuid4().hex[:12]}",
        objective=body.objective.strip(),
        constraints=tuple(c.strip() for c in body.constraints if str(c).strip()),
        priority=body.priority,
        context=dict(body.context),
        created_at=stamp,
    )
    try:
        graph = await rt.decomposition.decompose(
            goal, max_depth=body.max_depth, now=stamp
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return graph_to_response(graph)


@router.get(
    "/graphs/{graph_id}",
    response_model=TaskGraphResponse,
    summary="Fetch a task graph",
)
async def get_graph(graph_id: str) -> TaskGraphResponse:
    rt = get_aether_runtime()
    graph = await rt.decomposition.get(graph_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="task graph not found")
    return graph_to_response(graph)


@router.post(
    "/reflect",
    response_model=ReflectionResponse,
    summary="Reflect on reasoning and optionally revise plan (Module 3)",
)
async def reflect(body: ReflectRequest) -> ReflectionResponse:
    rt = get_aether_runtime()
    plan = await rt.planning.get(body.plan_id)
    if plan is None:
        plan = await rt.attention.get_plan(body.plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="cognition plan not found")
    try:
        reflection, revised = await rt.cognition.reflect(
            plan,
            reasoning_summary=body.reasoning_summary,
            evidence=body.evidence,
            revise=body.revise,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return reflection_to_response(reflection, revised_plan=revised)


@router.post(
    "/critique",
    response_model=CritiqueResponse,
    summary="Structured self-critique (Module 4)",
)
async def critique(body: CritiqueRequest) -> CritiqueResponse:
    rt = get_aether_runtime()
    plan = await rt.planning.get(body.plan_id)
    if plan is None:
        plan = await rt.attention.get_plan(body.plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="cognition plan not found")
    reflection = None
    if body.reflection_id:
        reflection = await rt.reflection.get(body.reflection_id)
    try:
        result = await rt.cognition.critique(
            plan,
            reasoning_summary=body.reasoning_summary,
            evidence=body.evidence,
            reflection=reflection,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return critique_to_response(result)


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
