"""Evaluate candidate strategies via the Simulation Engine.

Returns immutable EvaluatedStrategy results. Never modifies the OS.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from aetheros.intent.models import IntentProfile
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.research.models import CandidateStrategy, EvaluatedStrategy
from aetheros.simulation import SimulatableStrategy, SimulationEngine


@dataclass
class StrategyEvaluator:
    """Run every candidate through the Simulation Engine.

    Args:
        simulator: Simulation backend used for what-if scoring.
    """

    simulator: SimulationEngine = field(default_factory=SimulationEngine)

    def evaluate(
        self,
        strategy: CandidateStrategy,
        snapshot: TelemetrySnapshot,
        intent: IntentProfile,
    ) -> EvaluatedStrategy:
        """Simulate one strategy and wrap the immutable result."""

        sim_input = SimulatableStrategy(
            title=strategy.title,
            description=strategy.description,
            expected_cpu_delta=strategy.expected_cpu_delta,
            expected_memory_delta=strategy.expected_memory_delta,
            expected_efficiency_delta=strategy.expected_efficiency_delta,
        )
        result = self.simulator.simulate(sim_input, snapshot, intent)
        return EvaluatedStrategy(strategy=strategy, simulation=result)

    def evaluate_all(
        self,
        strategies: Sequence[CandidateStrategy],
        snapshot: TelemetrySnapshot,
        intent: IntentProfile,
    ) -> tuple[EvaluatedStrategy, ...]:
        """Simulate every strategy and return immutable results."""

        return tuple(
            self.evaluate(strategy, snapshot, intent) for strategy in strategies
        )
