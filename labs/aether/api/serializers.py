"""Serialization helpers for Aether API responses."""

from __future__ import annotations

from labs.aether.api.schemas import (
    AttentionAllocationResponse,
    AttentionSignalsOut,
    CognitionPlanResponse,
    CognitionStageOut,
)
from labs.aether.models.types import AttentionAllocation, CognitionPlan


def allocation_to_response(allocation: AttentionAllocation) -> AttentionAllocationResponse:
    return AttentionAllocationResponse(
        id=allocation.id,
        goal_id=allocation.goal_id,
        signals=AttentionSignalsOut(
            task_complexity=allocation.signals.task_complexity,
            available_context=allocation.signals.available_context,
            memory_relevance=allocation.signals.memory_relevance,
            uncertainty=allocation.signals.uncertainty,
        ),
        weights={k: float(v) for k, v in allocation.weights.items()},
        reasoning_budget=allocation.reasoning_budget,
        retrieval_budget=allocation.retrieval_budget,
        factors=list(allocation.factors),
        confidence=allocation.confidence,
        created_at=allocation.created_at,
    )


def plan_to_response(
    plan: CognitionPlan,
    *,
    attention: AttentionAllocation | None = None,
) -> CognitionPlanResponse:
    return CognitionPlanResponse(
        id=plan.id,
        goal_id=plan.goal_id,
        complexity=plan.complexity,
        attention_budget=plan.attention_budget,
        stages=[
            CognitionStageOut(
                name=s.name,
                description=s.description,
                attention_share=s.attention_share,
            )
            for s in plan.stages
        ],
        confidence=plan.confidence,
        attention_id=plan.attention_id,
        status=plan.status,
        created_at=plan.created_at,
        attention=allocation_to_response(attention) if attention else None,
    )
