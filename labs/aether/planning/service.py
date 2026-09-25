"""PlanningEngine service façade."""

from __future__ import annotations

from datetime import UTC, datetime

from labs.aether.models.types import (
    AttentionAllocation,
    CognitionPlan,
    Goal,
    TaskGraph,
)
from labs.aether.planning.planner import build_plan_from_graph, revise_plan
from labs.aether.repositories.plans import PlanRepository


class PlanningEngine:
    """Async façade for hierarchical cognition planning."""

    def __init__(self, *, repo: PlanRepository | None = None) -> None:
        self._repo = repo if repo is not None else PlanRepository()

    @property
    def repo(self) -> PlanRepository:
        return self._repo

    async def plan(
        self,
        goal: Goal,
        allocation: AttentionAllocation,
        graph: TaskGraph,
        *,
        now: datetime | None = None,
    ) -> CognitionPlan:
        stamp = now or datetime.now(UTC)
        plan = build_plan_from_graph(goal, allocation, graph, now=stamp)
        await self._repo.append(plan)
        return plan

    async def revise(
        self,
        plan: CognitionPlan,
        *,
        improvements: tuple[str, ...],
        now: datetime | None = None,
    ) -> CognitionPlan:
        revised = revise_plan(plan, improvements=improvements, now=now)
        await self._repo.append(revised)
        return revised

    async def get(self, plan_id: str) -> CognitionPlan | None:
        return await self._repo.get(plan_id)
