"""Simulation Engine — what-if scoring with no OS side effects.

Applies candidate strategy deltas to a telemetry snapshot in pure math.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.intent.models import IntentProfile
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.simulation.models import SimulationResult


@dataclass(frozen=True, slots=True)
class SimulatableStrategy:
    """Minimal strategy shape required by the simulator.

    Research CandidateStrategy satisfies this structurally.
    """

    title: str
    description: str
    expected_cpu_delta: float
    expected_memory_delta: float
    expected_efficiency_delta: float


@dataclass
class SimulationEngine:
    """Run read-only what-if simulations for candidate strategies."""

    def simulate(
        self,
        strategy: SimulatableStrategy,
        snapshot: TelemetrySnapshot,
        intent: IntentProfile,
    ) -> SimulationResult:
        """Simulate one strategy against the current snapshot and intent.

        Args:
            strategy: Candidate strategy with expected deltas.
            snapshot: Current telemetry (read-only input).
            intent: Active user intent profile.

        Returns:
            An immutable SimulationResult. Never mutates the OS.
        """

        projected_cpu = _clamp(
            snapshot.cpu_percent + strategy.expected_cpu_delta, 0.0, 100.0
        )
        projected_mem = _clamp(
            snapshot.memory_percent + strategy.expected_memory_delta, 0.0, 100.0
        )

        cpu_relief = max(0.0, snapshot.cpu_percent - projected_cpu)
        mem_relief = max(0.0, snapshot.memory_percent - projected_mem)

        # Performance: responsiveness + intent CPU/latency alignment.
        performance = 55.0 + cpu_relief * 1.8
        performance += intent.latency_weight * 0.35
        performance += intent.cpu_weight * 0.15
        if (
            "interactive" in strategy.title.lower()
            or "priority" in strategy.title.lower()
        ):
            performance += intent.latency_weight * 0.45
            performance += 8.0

        # Stability: prefer avoiding extreme projected load.
        stability = 72.0
        stability -= max(0.0, projected_cpu - 80.0) * 0.8
        stability -= max(0.0, projected_mem - 85.0) * 0.6
        stability += mem_relief * 0.9
        if "interactive" in strategy.title.lower():
            stability += 12.0
            performance += 4.0
        if abs(strategy.expected_cpu_delta) > 25:
            stability -= 8.0  # aggressive swings look less stable

        # Efficiency: explicit efficiency delta + battery-oriented intent.
        efficiency = 50.0 + strategy.expected_efficiency_delta * 2.0
        efficiency += intent.efficiency_weight * 0.4
        if "power" in strategy.title.lower() or "efficient" in strategy.title.lower():
            efficiency += 10.0

        performance = _clamp(performance, 0.0, 100.0)
        stability = _clamp(stability, 0.0, 100.0)
        efficiency = _clamp(efficiency, 0.0, 100.0)
        overall = _clamp(
            (performance * 0.4) + (stability * 0.35) + (efficiency * 0.25),
            0.0,
            100.0,
        )

        notes = (
            f"Projected CPU {projected_cpu:.0f}% / Memory {projected_mem:.0f}% "
            f"under intent '{intent.name}'."
        )
        return SimulationResult(
            strategy_title=strategy.title,
            performance_score=round(performance, 1),
            stability_score=round(stability, 1),
            efficiency_score=round(efficiency, 1),
            overall_improvement=round(overall, 1),
            projected_cpu_percent=round(projected_cpu, 1),
            projected_memory_percent=round(projected_mem, 1),
            notes=notes,
        )


def _clamp(value: float, low: float, high: float) -> float:
    """Clamp a float into [low, high]."""

    return max(low, min(high, value))
