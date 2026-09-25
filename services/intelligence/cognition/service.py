"""CognitionEngine — public understand() interface."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from services.intelligence.cognition.allocate import allocate_resources
from services.intelligence.cognition.complexity import estimate_complexity
from services.intelligence.cognition.decompose import decompose_goal
from services.intelligence.models.common import new_id
from services.intelligence.models.types import CognitionPlan, IntelligenceHealth
from services.intelligence.repositories.cognition import InMemoryCognitionPlanRepository


class CognitionEngine:
    """Understand objectives, decompose problems, allocate reasoning resources.

    Deterministic and model-agnostic. Performs aggregation and structural
    planning only — no prediction and no foundation-model calls.
    """

    def __init__(
        self,
        *,
        plans: InMemoryCognitionPlanRepository | None = None,
    ) -> None:
        self._plans = plans or InMemoryCognitionPlanRepository()

    @property
    def plans(self) -> InMemoryCognitionPlanRepository:
        return self._plans

    async def understand(
        self,
        goal: str,
        context: Mapping[str, Any] | None = None,
        constraints: Sequence[str] = (),
        *,
        workspace_id: str = "default",
        created_by: str = "system",
    ) -> CognitionPlan:
        """Produce and persist an immutable cognition plan."""

        ctx = dict(context or {})
        constraint_tuple = tuple(
            " ".join(str(c).split()).strip()
            for c in constraints
            if str(c).strip()
        )
        objectives = decompose_goal(goal, constraints=constraint_tuple, context=ctx)
        allocation = allocate_resources(
            goal,
            context=ctx,
            constraints=constraint_tuple,
            objective_count=len(objectives),
        )
        complexity = estimate_complexity(
            objectives,
            constraint_count=len(constraint_tuple),
            context_keys=len(ctx),
            agent_count=len(allocation.required_agents),
            knowledge_count=len(allocation.required_knowledge),
        )
        steps = _execution_steps(objectives, allocation)
        confidence = _confidence(
            objectives=objectives,
            constraints=constraint_tuple,
            allocation_agents=len(allocation.required_agents),
            complexity_score=complexity.score,
        )
        plan = CognitionPlan(
            id=new_id(),
            workspace_id=workspace_id,
            goal=" ".join(goal.split()).strip(),
            context=ctx,
            constraints=constraint_tuple,
            objectives=objectives,
            complexity=complexity,
            allocation=allocation,
            execution_steps=steps,
            confidence=confidence,
            created_by=created_by,
            created_at=datetime.now(UTC),
            status="planned",
        )
        return await self._plans.append(plan)

    async def get(self, plan_id: str) -> CognitionPlan | None:
        """Fetch a previously stored plan."""

        return await self._plans.get(plan_id)

    async def list(
        self,
        *,
        workspace_id: str,
        limit: int = 50,
    ) -> Sequence[CognitionPlan]:
        """List plans for a workspace."""

        return await self._plans.list(workspace_id=workspace_id, limit=limit)

    async def health(self, *, workspace_id: str) -> IntelligenceHealth:
        """Aggregate intelligence health for a workspace."""

        items = await self._plans.list(workspace_id=workspace_id, limit=10_000)
        if not items:
            return IntelligenceHealth(
                plan_count=0,
                avg_confidence=0.0,
                last_plan_at=None,
                workspace_id=workspace_id,
            )
        avg = sum(p.confidence for p in items) / len(items)
        last = max(p.created_at for p in items)
        return IntelligenceHealth(
            plan_count=len(items),
            avg_confidence=round(avg, 4),
            last_plan_at=last,
            workspace_id=workspace_id,
        )


def _execution_steps(objectives: Sequence[Any], allocation: Any) -> tuple[str, ...]:
    steps: list[str] = [
        "Validate objective and constraints",
        "Decompose into objective tree",
        "Estimate structural complexity",
        "Allocate agents and knowledge domains",
    ]
    for node in objectives:
        if node.depth == 1:
            steps.append(f"Address: {node.statement}")
    if allocation.required_agents:
        steps.append(
            "Engage agents: " + ", ".join(allocation.required_agents)
        )
    if allocation.required_knowledge:
        steps.append(
            "Load knowledge: " + ", ".join(allocation.required_knowledge)
        )
    steps.append("Hand off to hierarchical planner (Module 2)")
    return tuple(steps)


def _confidence(
    *,
    objectives: Sequence[Any],
    constraints: Sequence[str],
    allocation_agents: int,
    complexity_score: float,
) -> float:
    coverage = min(1.0, len(objectives) / 3.0)
    constraint_fit = 1.0 if not constraints else min(1.0, 0.6 + 0.1 * len(constraints))
    evidence = 0.55 + 0.1 * min(3, allocation_agents)
    # Higher complexity slightly reduces confidence without evidence explosion.
    complexity_penalty = 0.08 * complexity_score
    raw = 0.35 * coverage + 0.25 * constraint_fit + 0.40 * evidence - complexity_penalty
    return round(max(0.05, min(0.99, raw)), 4)
