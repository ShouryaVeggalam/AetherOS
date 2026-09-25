"""Aether Lab composition root."""

from __future__ import annotations

from labs.aether.attention.service import AttentionEngine
from labs.aether.cognition.service import CognitionEngine
from labs.aether.critique.service import CritiqueEngine
from labs.aether.decomposition.service import DecompositionEngine
from labs.aether.models.types import AetherHealth
from labs.aether.planning.service import PlanningEngine
from labs.aether.reflection.service import ReflectionEngine
from labs.aether.repositories.attention import AttentionRepository
from labs.aether.repositories.critiques import CritiqueRepository
from labs.aether.repositories.plans import PlanRepository
from labs.aether.repositories.reflections import ReflectionRepository
from labs.aether.repositories.tasks import TaskGraphRepository


class AetherRuntime:
    """Shared runtime for Aether Lab services."""

    def __init__(
        self,
        *,
        attention_repo: AttentionRepository | None = None,
        plan_repo: PlanRepository | None = None,
        task_repo: TaskGraphRepository | None = None,
        reflection_repo: ReflectionRepository | None = None,
        critique_repo: CritiqueRepository | None = None,
    ) -> None:
        self.attention_repo = (
            attention_repo if attention_repo is not None else AttentionRepository()
        )
        self.plan_repo = plan_repo if plan_repo is not None else PlanRepository()
        self.task_repo = task_repo if task_repo is not None else TaskGraphRepository()
        self.reflection_repo = (
            reflection_repo
            if reflection_repo is not None
            else ReflectionRepository()
        )
        self.critique_repo = (
            critique_repo if critique_repo is not None else CritiqueRepository()
        )
        self.attention = AttentionEngine(
            attention_repo=self.attention_repo,
            plan_repo=self.plan_repo,
        )
        self.decomposition = DecompositionEngine(repo=self.task_repo)
        self.planning = PlanningEngine(repo=self.plan_repo)
        self.reflection = ReflectionEngine(repo=self.reflection_repo)
        self.critique = CritiqueEngine(repo=self.critique_repo)
        self.cognition = CognitionEngine(
            attention=self.attention,
            decomposition=self.decomposition,
            planning=self.planning,
            reflection=self.reflection,
            critique=self.critique,
        )

    async def health(self) -> AetherHealth:
        return AetherHealth(
            attention_count=len(self.attention_repo),
            plan_count=len(self.plan_repo),
            task_graph_count=len(self.task_repo),
            reflection_count=len(self.reflection_repo),
            critique_count=len(self.critique_repo),
            modules_ready=(
                "attention",
                "decomposition",
                "planning",
                "reflection",
                "critique",
            ),
            status="ok",
        )


_RUNTIME: AetherRuntime | None = None


def get_aether_runtime() -> AetherRuntime:
    """Return the process-wide Aether runtime (lazy singleton)."""

    global _RUNTIME
    if _RUNTIME is None:
        _RUNTIME = AetherRuntime()
    return _RUNTIME


def reset_aether_runtime(runtime: AetherRuntime | None = None) -> AetherRuntime:
    """Replace the singleton (tests)."""

    global _RUNTIME
    _RUNTIME = runtime if runtime is not None else AetherRuntime()
    return _RUNTIME
