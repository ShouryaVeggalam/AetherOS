"""Research Agent — simulate alternative strategies (what-if).

Responsibility: score lightweight alternate postures via SimulationEngine.
Never applies strategies to the OS.
"""

from __future__ import annotations

from aetheros.agents.base import AgentFinding, BaseAgent, DeliberationContext
from aetheros.messaging import AsyncMessageBus
from aetheros.simulation.engine import SimulatableStrategy, SimulationEngine

_CANDIDATES: tuple[SimulatableStrategy, ...] = (
    SimulatableStrategy(
        title="Performance Priority",
        description="Bias scheduling toward interactive responsiveness.",
        expected_cpu_delta=-8.0,
        expected_memory_delta=-2.0,
        expected_efficiency_delta=-6.0,
    ),
    SimulatableStrategy(
        title="Efficiency Priority",
        description="Bias toward lower power and background deferral.",
        expected_cpu_delta=-15.0,
        expected_memory_delta=-5.0,
        expected_efficiency_delta=12.0,
    ),
    SimulatableStrategy(
        title="Balanced Mode",
        description="Moderate relief with limited efficiency cost.",
        expected_cpu_delta=-10.0,
        expected_memory_delta=-3.0,
        expected_efficiency_delta=4.0,
    ),
)


class ResearchAgent(BaseAgent):
    """Simulate candidate strategies and recommend the best score."""

    def __init__(
        self,
        bus: AsyncMessageBus,
        *,
        simulator: SimulationEngine | None = None,
    ) -> None:
        """Bind to the shared bus and optional simulation engine."""

        super().__init__(agent_id="research", bus=bus)
        self.simulator = simulator or SimulationEngine()

    def analyze(self, context: DeliberationContext) -> AgentFinding:
        """Run what-if simulations and pick the highest composite score."""

        scored: list[tuple[str, float, float, float]] = []
        for strategy in _CANDIDATES:
            result = self.simulator.simulate(strategy, context.snapshot, context.intent)
            composite = (
                result.performance_score * 0.4
                + result.stability_score * 0.3
                + result.efficiency_score * 0.3
            )
            scored.append(
                (
                    strategy.title,
                    composite,
                    result.performance_score,
                    result.efficiency_score,
                )
            )
        scored.sort(key=lambda row: row[1], reverse=True)
        winner_title, winner_score, perf, eff = scored[0]
        evidence = tuple(
            f"{title}: score {score:.1f} (perf {p:.1f} / eff {e:.1f})"
            for title, score, p, e in scored
        )
        stance_map = {
            "Performance Priority": "prefer_performance",
            "Efficiency Priority": "prefer_efficiency",
            "Balanced Mode": "prefer_balanced",
        }
        return AgentFinding(
            agent_id=self.agent_id,
            stance=stance_map.get(winner_title, "prefer_balanced"),
            summary=f"Simulation favors {winner_title} (score {winner_score:.1f}).",
            confidence=min(0.95, 0.55 + winner_score / 200.0),
            priority=0.5,
            metrics={
                "winner_score": round(winner_score, 2),
                "performance_score": round(perf, 2),
                "efficiency_score": round(eff, 2),
            },
            evidence=evidence,
            status="ok",
        )
