"""Simulation-engine data contracts (minimal Phase 8 support).

All results are hypothetical — simulations never change the host OS.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Immutable outcome of simulating one candidate strategy.

    Attributes:
        strategy_title: Strategy that was simulated.
        performance_score: 0–100 estimated performance.
        stability_score: 0–100 estimated stability.
        efficiency_score: 0–100 estimated efficiency.
        overall_improvement: Aggregate improvement estimate (0–100).
        projected_cpu_percent: Estimated CPU after applying the strategy.
        projected_memory_percent: Estimated memory after applying the strategy.
        notes: Short explanation of the simulated outcome.
    """

    strategy_title: str
    performance_score: float
    stability_score: float
    efficiency_score: float
    overall_improvement: float
    projected_cpu_percent: float
    projected_memory_percent: float
    notes: str

    def __post_init__(self) -> None:
        """Clamp score fields conceptually via validation."""

        for name in (
            "performance_score",
            "stability_score",
            "efficiency_score",
            "overall_improvement",
        ):
            value = getattr(self, name)
            if not 0.0 <= float(value) <= 100.0:
                raise ValueError(f"{name} must be between 0 and 100")
