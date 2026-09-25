"""Append-only reflection repository."""

from __future__ import annotations

from collections.abc import Sequence

from labs.aether.models.types import Reflection


class ReflectionRepository:
    """In-memory append-only store for reflections."""

    def __init__(self) -> None:
        self._items: dict[str, Reflection] = {}

    async def append(self, reflection: Reflection) -> Reflection:
        if not reflection.id.strip():
            raise ValueError("reflection id must be non-empty")
        if reflection.id in self._items:
            raise ValueError(f"reflection already exists: {reflection.id}")
        self._items[reflection.id] = reflection
        return reflection

    async def get(self, reflection_id: str) -> Reflection | None:
        return self._items.get(reflection_id)

    async def list_for_plan(
        self,
        plan_id: str,
        *,
        limit: int = 50,
    ) -> Sequence[Reflection]:
        items = [r for r in self._items.values() if r.plan_id == plan_id]
        items.sort(key=lambda r: r.created_at or r.id, reverse=True)
        return items[: max(0, limit)]

    def __len__(self) -> int:
        return len(self._items)
