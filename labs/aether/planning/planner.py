"""Hierarchical planning — builds CognitionPlan from attention + task graph."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from labs.aether.models.types import (
    AttentionAllocation,
    CognitionPlan,
    CognitionStage,
    ComplexityTier,
    Goal,
    TaskGraph,
)


def build_plan_from_graph(
    goal: Goal,
    allocation: AttentionAllocation,
    graph: TaskGraph,
    *,
    now: datetime | None = None,
    plan_id: str | None = None,
    parent_plan_id: str = "",
    status: str = "active",
) -> CognitionPlan:
    """Compose an active cognition plan from attention + DAG."""

    stamp = now or datetime.now(UTC)
    complexity = _tier(allocation.signals.task_complexity, graph)
    stages = _stages(allocation, graph)
    confidence = round(
        min(
            0.99,
            allocation.confidence * 0.7
            + min(1.0, len(graph.tasks) / 12.0) * 0.2
            + 0.1,
        ),
        4,
    )
    return CognitionPlan(
        id=plan_id or f"plan_{uuid4().hex[:12]}",
        goal_id=goal.id,
        complexity=complexity,
        attention_budget=allocation.reasoning_budget,
        stages=stages,
        confidence=confidence,
        attention_id=allocation.id,
        task_graph_id=graph.id,
        status=status,  # type: ignore[arg-type]
        created_at=stamp,
        parent_plan_id=parent_plan_id,
    )


def revise_plan(
    plan: CognitionPlan,
    *,
    improvements: tuple[str, ...],
    now: datetime | None = None,
) -> CognitionPlan:
    """Produce a revised plan record (append-only; parent linked)."""

    stamp = now or datetime.now(UTC)
    extra = tuple(
        CognitionStage(
            name=f"improvement_{idx + 1}",
            description=text[:200],
            attention_share=round(0.05 + 0.02 * min(idx, 3), 4),
        )
        for idx, text in enumerate(improvements[:4])
    )
    stages = plan.stages + extra
    return CognitionPlan(
        id=f"plan_{uuid4().hex[:12]}",
        goal_id=plan.goal_id,
        complexity=plan.complexity,
        attention_budget=min(1.0, plan.attention_budget + 0.05),
        stages=stages,
        confidence=round(min(0.99, plan.confidence + 0.03), 4),
        attention_id=plan.attention_id,
        task_graph_id=plan.task_graph_id,
        status="revised",
        created_at=stamp,
        parent_plan_id=plan.id,
    )


def _tier(complexity: float, graph: TaskGraph) -> ComplexityTier:
    depth_boost = min(0.2, graph.max_depth * 0.05)
    score = complexity + depth_boost
    if score < 0.25:
        return "trivial"
    if score < 0.5:
        return "moderate"
    if score < 0.75:
        return "complex"
    return "strategic"


def _stages(
    allocation: AttentionAllocation,
    graph: TaskGraph,
) -> tuple[CognitionStage, ...]:
    weights = allocation.weights
    by_type: dict[str, int] = {}
    for task in graph.tasks:
        by_type[task.type] = by_type.get(task.type, 0) + 1
    return (
        CognitionStage(
            name="attention",
            description="Allocate cognitive resources",
            attention_share=round(float(weights.get("focus", 0.25)), 4),
        ),
        CognitionStage(
            name="decomposition",
            description=f"DAG with {len(graph.tasks)} tasks",
            attention_share=round(float(weights.get("exploration", 0.25)), 4),
        ),
        CognitionStage(
            name="strategic",
            description=f"{by_type.get('strategic', 0)} strategic nodes",
            attention_share=0.1,
        ),
        CognitionStage(
            name="tactical",
            description=f"{by_type.get('tactical', 0)} tactical nodes",
            attention_share=0.1,
        ),
        CognitionStage(
            name="reasoning",
            description="Execute reasoning within budget",
            attention_share=round(float(weights.get("focus", 0.25)) * 0.4, 4),
        ),
        CognitionStage(
            name="reflection",
            description="Identify gaps and assumptions",
            attention_share=round(float(weights.get("verification", 0.25)) * 0.4, 4),
        ),
        CognitionStage(
            name="critique",
            description="Structured self-evaluation",
            attention_share=round(float(weights.get("verification", 0.25)) * 0.4, 4),
        ),
    )
