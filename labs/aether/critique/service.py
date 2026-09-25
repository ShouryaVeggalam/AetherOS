"""CritiqueEngine service façade."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from labs.aether.critique.engine import critique_reasoning
from labs.aether.models.types import CognitionPlan, Critique, Reflection
from labs.aether.repositories.critiques import CritiqueRepository


class CritiqueEngine:
    """Async façade for structured self-critique."""

    def __init__(self, *, repo: CritiqueRepository | None = None) -> None:
        self._repo = repo if repo is not None else CritiqueRepository()

    @property
    def repo(self) -> CritiqueRepository:
        return self._repo

    async def critique(
        self,
        plan: CognitionPlan,
        *,
        reasoning_summary: str,
        evidence: Sequence[str] = (),
        reflection: Reflection | None = None,
        now: datetime | None = None,
    ) -> Critique:
        stamp = now or datetime.now(UTC)
        result = critique_reasoning(
            plan=plan,
            reasoning_summary=reasoning_summary,
            evidence=evidence,
            reflection=reflection,
            now=stamp,
        )
        await self._repo.append(result)
        return result

    async def get(self, critique_id: str) -> Critique | None:
        return await self._repo.get(critique_id)
