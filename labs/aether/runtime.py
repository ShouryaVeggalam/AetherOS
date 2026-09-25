"""Aether Lab composition root."""

from __future__ import annotations

from labs.aether.attention.service import AttentionEngine
from labs.aether.models.types import AetherHealth
from labs.aether.repositories.attention import AttentionRepository
from labs.aether.repositories.plans import PlanRepository


class AetherRuntime:
    """Shared runtime for Aether Lab services."""

    def __init__(
        self,
        *,
        attention: AttentionEngine | None = None,
        attention_repo: AttentionRepository | None = None,
        plan_repo: PlanRepository | None = None,
    ) -> None:
        self.attention_repo = (
            attention_repo if attention_repo is not None else AttentionRepository()
        )
        self.plan_repo = plan_repo if plan_repo is not None else PlanRepository()
        self.attention = (
            attention
            if attention is not None
            else AttentionEngine(
                attention_repo=self.attention_repo,
                plan_repo=self.plan_repo,
            )
        )

    async def health(self) -> AetherHealth:
        return AetherHealth(
            attention_count=len(self.attention_repo),
            plan_count=len(self.plan_repo),
            modules_ready=("attention",),
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
