"""Append-only cognition plan repository (in-memory)."""

from __future__ import annotations

from collections.abc import Sequence

from services.intelligence.models.types import CognitionPlan


class InMemoryCognitionPlanRepository:
    """Workspace-scoped append-only store for cognition plans.

    Historical plans are never updated or deleted. Callers receive the
    same frozen instances that were appended.
    """

    def __init__(self) -> None:
        self._items: dict[str, CognitionPlan] = {}

    async def append(self, plan: CognitionPlan) -> CognitionPlan:
        """Persist a plan. Raises if the id already exists."""

        if plan.id in self._items:
            raise ValueError(f"cognition plan already exists: {plan.id}")
        self._items[plan.id] = plan
        return plan

    async def get(self, plan_id: str) -> CognitionPlan | None:
        """Fetch a plan by id, or None."""

        return self._items.get(plan_id)

    async def list(
        self,
        *,
        workspace_id: str,
        limit: int = 50,
    ) -> Sequence[CognitionPlan]:
        """List plans for a workspace, newest first."""

        items = [p for p in self._items.values() if p.workspace_id == workspace_id]
        items.sort(key=lambda p: p.created_at, reverse=True)
        return items[: max(0, limit)]

    def __len__(self) -> int:
        return len(self._items)
