"""Append-only cognition plan repository."""

from __future__ import annotations

from collections.abc import Sequence

from labs.aether.models.types import CognitionPlan


class PlanRepository:
    """In-memory append-only store for cognition plans.

    Forward path: PostgreSQL table ``aether_cognition_plans``.
    """

    def __init__(self) -> None:
        self._items: dict[str, CognitionPlan] = {}

    async def append(self, plan: CognitionPlan) -> CognitionPlan:
        if plan.id in self._items:
            raise ValueError(f"cognition plan already exists: {plan.id}")
        self._items[plan.id] = plan
        return plan

    async def get(self, plan_id: str) -> CognitionPlan | None:
        return self._items.get(plan_id)

    async def list_for_goal(
        self,
        goal_id: str,
        *,
        limit: int = 50,
    ) -> Sequence[CognitionPlan]:
        items = [p for p in self._items.values() if p.goal_id == goal_id]
        items.sort(
            key=lambda p: p.created_at or p.id,
            reverse=True,
        )
        return items[: max(0, limit)]

    async def list_all(self, *, limit: int = 100) -> Sequence[CognitionPlan]:
        items = sorted(
            self._items.values(),
            key=lambda p: p.created_at or p.id,
            reverse=True,
        )
        return items[: max(0, limit)]

    def __len__(self) -> int:
        return len(self._items)
