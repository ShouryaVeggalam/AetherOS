"""ReflectionEngine service façade."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from labs.aether.models.types import CognitionPlan, Reflection
from labs.aether.reflection.engine import reflect_on_reasoning
from labs.aether.repositories.reflections import ReflectionRepository


class ReflectionEngine:
    """Async façade for post-reasoning reflection."""

    def __init__(self, *, repo: ReflectionRepository | None = None) -> None:
        self._repo = repo if repo is not None else ReflectionRepository()

    @property
    def repo(self) -> ReflectionRepository:
        return self._repo

    async def reflect(
        self,
        plan: CognitionPlan,
        *,
        reasoning_summary: str,
        evidence: Sequence[str] = (),
        now: datetime | None = None,
    ) -> Reflection:
        stamp = now or datetime.now(UTC)
        reflection = reflect_on_reasoning(
            plan=plan,
            reasoning_summary=reasoning_summary,
            evidence=evidence,
            now=stamp,
        )
        await self._repo.append(reflection)
        return reflection

    async def get(self, reflection_id: str) -> Reflection | None:
        return await self._repo.get(reflection_id)

    async def list_for_plan(self, plan_id: str) -> tuple[Reflection, ...]:
        return tuple(await self._repo.list_for_plan(plan_id))
