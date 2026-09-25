"""IntelligenceRuntime — DI composition root for GII Module 1+."""

from __future__ import annotations

from services.intelligence.cognition.service import CognitionEngine
from services.intelligence.repositories.cognition import InMemoryCognitionPlanRepository

_runtime: IntelligenceRuntime | None = None


class IntelligenceRuntime:
    """Shared repositories and engines for the General Intelligence Infrastructure."""

    def __init__(self) -> None:
        self.cognition_plans = InMemoryCognitionPlanRepository()
        self.cognition = CognitionEngine(plans=self.cognition_plans)


def get_intelligence_runtime() -> IntelligenceRuntime:
    """Return the process-local runtime singleton (lazy)."""

    global _runtime
    if _runtime is None:
        _runtime = IntelligenceRuntime()
    return _runtime


def reset_intelligence_runtime() -> None:
    """Drop the runtime singleton (tests only)."""

    global _runtime
    _runtime = None
