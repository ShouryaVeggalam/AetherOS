"""Serialization helpers for Aether API responses."""

from __future__ import annotations

from labs.aether.api.schemas import (
    AttentionAllocationResponse,
    AttentionSignalsOut,
    CognitionPlanResponse,
    CognitionStageOut,
    CritiqueResponse,
    CritiqueScoreOut,
    ReflectionResponse,
    TaskGraphResponse,
    TaskOut,
)
from labs.aether.decomposition.engine import topological_order
from labs.aether.models.types import (
    AttentionAllocation,
    CognitionPlan,
    Critique,
    Reflection,
    TaskGraph,
)


def allocation_to_response(
    allocation: AttentionAllocation,
) -> AttentionAllocationResponse:
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
        task_graph_id=plan.task_graph_id,
        status=plan.status,
        parent_plan_id=plan.parent_plan_id,
        created_at=plan.created_at,
        attention=allocation_to_response(attention) if attention else None,
    )


def graph_to_response(graph: TaskGraph) -> TaskGraphResponse:
    order = [t.id for t in topological_order(graph)]
    return TaskGraphResponse(
        id=graph.id,
        goal_id=graph.goal_id,
        objective=graph.objective,
        tasks=[
            TaskOut(
                id=t.id,
                parent_task=t.parent_task,
                type=t.type,
                dependencies=list(t.dependencies),
                status=t.status,
                statement=t.statement,
                depth=t.depth,
            )
            for t in graph.tasks
        ],
        roots=list(graph.roots),
        max_depth=graph.max_depth,
        created_at=graph.created_at,
        topo_order=order,
    )


def reflection_to_response(
    reflection: Reflection,
    *,
    revised_plan: CognitionPlan | None = None,
) -> ReflectionResponse:
    return ReflectionResponse(
        id=reflection.id,
        plan_id=reflection.plan_id,
        reasoning_summary=reflection.reasoning_summary,
        weaknesses=list(reflection.weaknesses),
        assumptions=list(reflection.assumptions),
        improvements=list(reflection.improvements),
        created_at=reflection.created_at,
        revised_plan=plan_to_response(revised_plan) if revised_plan else None,
    )


def critique_to_response(critique: Critique) -> CritiqueResponse:
    return CritiqueResponse(
        id=critique.id,
        plan_id=critique.plan_id,
        scores=[
            CritiqueScoreOut(
                criterion=s.criterion,
                score=s.score,
                notes=s.notes,
            )
            for s in critique.scores
        ],
        overall=critique.overall,
        verdict=critique.verdict,
        created_at=critique.created_at,
    )
