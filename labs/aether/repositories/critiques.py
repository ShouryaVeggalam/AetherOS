"""Append-only critique repository."""

from __future__ import annotations

from collections.abc import Sequence

from labs.aether.models.types import Critique


class CritiqueRepository:
    """In-memory append-only store for critiques."""

    def __init__(self) -> None:
        self._items: dict[str, Critique] = {}

    async def append(self, critique: Critique) -> Critique:
        if critique.id in self._items:
            raise ValueError(f"critique already exists: {critique.id}")
        self._items[critique.id] = critique
        return critique

    async def get(self, critique_id: str) -> Critique | None:
        return self._items.get(critique_id)

    async def list_for_plan(
        self,
        plan_id: str,
        *,
        limit: int = 50,
    ) -> Sequence[Critique]:
        items = [c for c in self._items.values() if c.plan_id == plan_id]
        items.sort(key=lambda c: c.created_at or c.id, reverse=True)
        return items[: max(0, limit)]

    def __len__(self) -> int:
        return len(self._items)
