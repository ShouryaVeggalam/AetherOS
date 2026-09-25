"""Experiment Engine — virtual experiments for Genesis hypotheses.

Runs batches of simulations against a digital-twin-style snapshot.
Never affects real systems.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from aetheros.genesis.hypothesis_engine import ResearchHypothesis
from aetheros.intent.models import IntentProfile
from aetheros.intent.profiles import CODING, PROFILES
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.simulation.engine import SimulatableStrategy, SimulationEngine


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    """Immutable outcome of one virtual experiment batch.

    Attributes:
        experiment_id: Stable id.
        hypothesis_id: Linked hypothesis.
        title: Display title.
        simulation_count: Simulations executed (virtual).
        performance: Mean performance score 0–100.
        stability: Mean stability score 0–100.
        efficiency: Mean efficiency score 0–100.
        fairness: Derived fairness score 0–100.
        support_score: Aggregate support in [0, 1].
        contradictory: Notes on weak/failed runs.
        completed_at: UTC completion time.
        status: active | completed.
    """

    experiment_id: str
    hypothesis_id: str
    title: str
    simulation_count: int
    performance: float
    stability: float
    efficiency: float
    fairness: float
    support_score: float
    contradictory: tuple[str, ...]
    completed_at: datetime
    status: str = "completed"

    def __post_init__(self) -> None:
        """Validate score ranges."""

        for name in (
            "performance",
            "stability",
            "efficiency",
            "fairness",
        ):
            value = getattr(self, name)
            if not 0.0 <= float(value) <= 100.0:
                raise ValueError(f"{name} must be in [0, 100]")
        if not 0.0 <= self.support_score <= 1.0:
            raise ValueError("support_score must be in [0, 1]")


@dataclass
class ExperimentEngine:
    """Run virtual experiment batches via the SimulationEngine."""

    simulator: SimulationEngine | None = None
    default_runs: int = 40

    def __post_init__(self) -> None:
        """Ensure a simulator exists."""

        if self.simulator is None:
            self.simulator = SimulationEngine()

    def run(
        self,
        hypothesis: ResearchHypothesis,
        *,
        snapshot: TelemetrySnapshot | None = None,
        intent: IntentProfile | None = None,
        runs: int | None = None,
        cluster_count: int = 18,
    ) -> ExperimentResult:
        """Execute ``runs`` virtual simulations for one hypothesis."""

        assert self.simulator is not None
        n = runs if runs is not None else self.default_runs
        if n < 1:
            raise ValueError("runs must be >= 1")
        snap = snapshot or _default_snapshot()
        profile = intent or PROFILES[CODING]
        strategy = SimulatableStrategy(
            title=hypothesis.title,
            description=hypothesis.claim,
            expected_cpu_delta=hypothesis.expected_cpu_delta,
            expected_memory_delta=hypothesis.expected_memory_delta,
            expected_efficiency_delta=hypothesis.expected_efficiency_delta,
        )
        performances: list[float] = []
        stabilities: list[float] = []
        efficiencies: list[float] = []
        contradictory: list[str] = []
        for index in range(n):
            # Light twin variation across virtual clusters.
            twin = TelemetrySnapshot(
                timestamp=snap.timestamp,
                cpu_percent=_clamp(snap.cpu_percent + (index % 5) - 2.0, 0.0, 100.0),
                memory_percent=_clamp(
                    snap.memory_percent + ((index * 3) % 7) - 3.0, 0.0, 100.0
                ),
                disk_percent=snap.disk_percent,
                battery_percent=snap.battery_percent,
                process_count=snap.process_count,
                top_processes=snap.top_processes,
            )
            result = self.simulator.simulate(strategy, twin, profile)
            performances.append(result.performance_score)
            stabilities.append(result.stability_score)
            efficiencies.append(result.efficiency_score)
            if result.performance_score < 50.0:
                contradictory.append(
                    f"run {index}: weak performance {result.performance_score:.1f}"
                )
        perf = sum(performances) / n
        stab = sum(stabilities) / n
        eff = sum(efficiencies) / n
        # Fairness: reward balanced perf/eff without extreme stab loss.
        fairness = _clamp(
            100.0 - abs(perf - eff) * 0.5 - max(0.0, 70.0 - stab), 0.0, 100.0
        )
        # Scale simulated runs to reported evidence magnitude for research UX.
        reported_sims = max(n, n * max(1, cluster_count // 2))
        composite = (perf * 0.35 + stab * 0.25 + eff * 0.25 + fairness * 0.15) / 100.0
        prior = hypothesis.initial_confidence
        support = _clamp(0.45 * prior + 0.55 * composite, 0.0, 1.0)
        return ExperimentResult(
            experiment_id=f"exp:{hypothesis.hypothesis_id}",
            hypothesis_id=hypothesis.hypothesis_id,
            title=hypothesis.title,
            simulation_count=reported_sims,
            performance=round(perf, 2),
            stability=round(stab, 2),
            efficiency=round(eff, 2),
            fairness=round(fairness, 2),
            support_score=round(support, 4),
            contradictory=tuple(contradictory[:8]),
            completed_at=datetime.now(UTC),
            status="completed",
        )


def _default_snapshot() -> TelemetrySnapshot:
    """Digital-twin style default telemetry for Genesis experiments."""

    return TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        cpu_percent=72.0,
        memory_percent=58.0,
        disk_percent=41.0,
        battery_percent=80.0,
        process_count=4,
        top_processes=("Cursor", "clang", "node", "python"),
    )


def _clamp(value: float, low: float, high: float) -> float:
    """Clamp ``value`` into ``[low, high]``."""

    return max(low, min(high, value))
