"""Twin planner — select and rank global digital-twin scenarios."""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.twin.simulator import (
    SEED_SCENARIOS,
    TwinOutcome,
    TwinScenario,
    TwinSimulator,
)


@dataclass(frozen=True, slots=True)
class TwinPlan:
    """Ranked twin outcomes with a recommended focus scenario."""

    outcomes: tuple[TwinOutcome, ...]
    recommended: TwinOutcome | None
    rationale: str


@dataclass
class TwinPlanner:
    """Plan which global twin scenarios to emphasize."""

    simulator: TwinSimulator | None = None

    def __post_init__(self) -> None:
        """Ensure simulator exists."""

        if self.simulator is None:
            self.simulator = TwinSimulator()

    def plan(
        self,
        scenarios: tuple[TwinScenario, ...] = SEED_SCENARIOS,
    ) -> TwinPlan:
        """Simulate all scenarios and rank by ascending risk (safer first)."""

        assert self.simulator is not None
        outcomes = tuple(self.simulator.simulate(s) for s in scenarios)
        # Prefer expansion (low risk) when available; else lowest risk.
        ranked = sorted(outcomes, key=lambda o: (o.risk, -o.capacity))
        recommended = ranked[0] if ranked else None
        rationale = (
            f"Recommended focus: {recommended.scenario.title} "
            f"(risk {recommended.risk:.0f}, capacity {recommended.capacity:.0f})."
            if recommended
            else "No scenarios planned."
        )
        rationale += " Humans approve any follow-up. Simulation only."
        return TwinPlan(
            outcomes=tuple(ranked),
            recommended=recommended,
            rationale=rationale,
        )
