"""Append-only task graph repository."""

from __future__ import annotations

from collections.abc import Sequence

from labs.aether.models.types import TaskGraph


class TaskGraphRepository:
    """In-memory append-only store for task graphs."""

    def __init__(self) -> None:
        self._items: dict[str, TaskGraph] = {}

    async def append(self, graph: TaskGraph) -> TaskGraph:
        if graph.id in self._items:
            raise ValueError(f"task graph already exists: {graph.id}")
        self._items[graph.id] = graph
        return graph

    async def get(self, graph_id: str) -> TaskGraph | None:
        return self._items.get(graph_id)

    async def list_for_goal(
        self,
        goal_id: str,
        *,
        limit: int = 50,
    ) -> Sequence[TaskGraph]:
        items = [g for g in self._items.values() if g.goal_id == goal_id]
        items.sort(key=lambda g: g.created_at or g.id, reverse=True)
        return items[: max(0, limit)]

    def __len__(self) -> int:
        return len(self._items)
