"""DecompositionEngine service façade."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from labs.aether.decomposition.engine import (
    decompose_objective,
    validate_dag,
)
from labs.aether.models.types import Goal, TaskGraph
from labs.aether.repositories.tasks import TaskGraphRepository


class DecompositionEngine:
    """Async façade for hierarchical objective decomposition."""

    def __init__(self, *, repo: TaskGraphRepository | None = None) -> None:
        self._repo = repo if repo is not None else TaskGraphRepository()

    @property
    def repo(self) -> TaskGraphRepository:
        return self._repo

    async def decompose(
        self,
        goal: Goal,
        *,
        max_depth: int = 3,
        now: datetime | None = None,
    ) -> TaskGraph:
        stamp = now or datetime.now(UTC)
        graph = decompose_objective(
            goal,
            max_depth=max_depth,
            now=stamp,
            graph_id=f"tg_{uuid4().hex[:12]}",
        )
        validate_dag(graph)
        await self._repo.append(graph)
        return graph

    async def get(self, graph_id: str) -> TaskGraph | None:
        return await self._repo.get(graph_id)
