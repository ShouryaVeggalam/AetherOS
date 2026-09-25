"""Append-only attention allocation repository."""

from __future__ import annotations

from collections.abc import Sequence

from labs.aether.models.types import AttentionAllocation


class AttentionRepository:
    """In-memory append-only store for attention allocations.

    Forward path: PostgreSQL table ``aether_attention_allocations``.
    Historical allocations are never mutated.
    """

    def __init__(self) -> None:
        self._items: dict[str, AttentionAllocation] = {}

    async def append(self, allocation: AttentionAllocation) -> AttentionAllocation:
        if allocation.id in self._items:
            raise ValueError(f"attention allocation already exists: {allocation.id}")
        self._items[allocation.id] = allocation
        return allocation

    async def get(self, allocation_id: str) -> AttentionAllocation | None:
        return self._items.get(allocation_id)

    async def list_for_goal(
        self,
        goal_id: str,
        *,
        limit: int = 50,
    ) -> Sequence[AttentionAllocation]:
        items = [a for a in self._items.values() if a.goal_id == goal_id]
        items.sort(key=lambda a: a.created_at, reverse=True)
        return items[: max(0, limit)]

    async def list_all(self, *, limit: int = 100) -> Sequence[AttentionAllocation]:
        items = sorted(
            self._items.values(),
            key=lambda a: a.created_at,
            reverse=True,
        )
        return items[: max(0, limit)]

    def __len__(self) -> int:
        return len(self._items)
