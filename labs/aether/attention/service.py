"""AttentionEngine — Module 1 of Aether Lab.

Allocates cognitive attention for a goal. Does not call foundation models.
Does not execute actions. Returns explainable ``AttentionAllocation`` records.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from labs.aether.attention.allocator import allocate_attention
from labs.aether.attention.signals import derive_signals
from labs.aether.models.types import (
    AttentionAllocation,
    AttentionSignals,
    CognitionPlan,
    CognitionStage,
    ComplexityTier,
    Goal,
)
from labs.aether.repositories.attention import AttentionRepository
from labs.aether.repositories.plans import PlanRepository


class AttentionEngine:
    """Async service facade for adaptive attention allocation."""

    def __init__(
        self,
        *,
        attention_repo: AttentionRepository | None = None,
        plan_repo: PlanRepository | None = None,
    ) -> None:
        self._attention = (
            attention_repo if attention_repo is not None else AttentionRepository()
        )
        self._plans = plan_repo if plan_repo is not None else PlanRepository()

    @property
    def attention_repo(self) -> AttentionRepository:
        return self._attention

    @property
    def plan_repo(self) -> PlanRepository:
        return self._plans

    async def allocate(
        self,
        goal: Goal,
        *,
        task_complexity: float | None = None,
        available_context: float | None = None,
        memory_relevance: float | None = None,
        uncertainty: float | None = None,
        signals: AttentionSignals | None = None,
        now: datetime | None = None,
    ) -> AttentionAllocation:
        """Derive signals (unless provided) and persist an allocation."""

        stamp = now or datetime.now(UTC)
        resolved = signals or derive_signals(
            goal,
            task_complexity=task_complexity,
            available_context=available_context,
            memory_relevance=memory_relevance,
            uncertainty=uncertainty,
        )
        allocation = allocate_attention(
            resolved,
            goal_id=goal.id,
            now=stamp,
        )
        await self._attention.append(allocation)
        return allocation

    async def allocate_from_objective(
        self,
        objective: str,
        *,
        constraints: Sequence[str] = (),
        priority: float = 50.0,
        context: Mapping[str, Any] | None = None,
        goal_id: str | None = None,
        now: datetime | None = None,
        **signal_overrides: float | None,
    ) -> tuple[Goal, AttentionAllocation]:
        """Convenience: build a Goal then allocate attention."""

        stamp = now or datetime.now(UTC)
        goal = Goal(
            id=goal_id or f"goal_{uuid4().hex[:12]}",
            objective=objective.strip(),
            constraints=tuple(c.strip() for c in constraints if str(c).strip()),
            priority=float(priority),
            context=dict(context or {}),
            created_at=stamp,
        )
        allocation = await self.allocate(
            goal,
            now=stamp,
            task_complexity=signal_overrides.get("task_complexity"),
            available_context=signal_overrides.get("available_context"),
            memory_relevance=signal_overrides.get("memory_relevance"),
            uncertainty=signal_overrides.get("uncertainty"),
        )
        return goal, allocation

    async def draft_plan(
        self,
        goal: Goal,
        allocation: AttentionAllocation,
        *,
        now: datetime | None = None,
    ) -> CognitionPlan:
        """Produce a draft CognitionPlan from an attention allocation.

        Full hierarchical planning is Module 2+. This draft stages attention
        shares across the cognitive pipeline so observatory views have a plan.
        """

        stamp = now or datetime.now(UTC)
        complexity = _tier(allocation.signals.task_complexity)
        stages = _stages(allocation)
        plan = CognitionPlan(
            id=f"plan_{uuid4().hex[:12]}",
            goal_id=goal.id,
            complexity=complexity,
            attention_budget=allocation.reasoning_budget,
            stages=stages,
            confidence=allocation.confidence,
            attention_id=allocation.id,
            status="draft",
            created_at=stamp,
        )
        await self._plans.append(plan)
        return plan

    async def get_allocation(self, allocation_id: str) -> AttentionAllocation | None:
        return await self._attention.get(allocation_id)

    async def get_plan(self, plan_id: str) -> CognitionPlan | None:
        return await self._plans.get(plan_id)


def _tier(complexity: float) -> ComplexityTier:
    if complexity < 0.25:
        return "trivial"
    if complexity < 0.5:
        return "moderate"
    if complexity < 0.75:
        return "complex"
    return "strategic"


def _stages(allocation: AttentionAllocation) -> tuple[CognitionStage, ...]:
    weights = allocation.weights
    return (
        CognitionStage(
            name="attention",
            description="Allocate cognitive resources",
            attention_share=round(float(weights.get("focus", 0.25)), 4),
        ),
        CognitionStage(
            name="decomposition",
            description="Hierarchical problem breakdown",
            attention_share=round(float(weights.get("exploration", 0.25)), 4),
        ),
        CognitionStage(
            name="reasoning",
            description="Execute reasoning within budget",
            attention_share=round(float(weights.get("focus", 0.25)) * 0.5, 4),
        ),
        CognitionStage(
            name="reflection",
            description="Identify gaps and assumptions",
            attention_share=round(float(weights.get("verification", 0.25)) * 0.5, 4),
        ),
        CognitionStage(
            name="critique",
            description="Structured self-evaluation",
            attention_share=round(float(weights.get("verification", 0.25)) * 0.5, 4),
        ),
    )
