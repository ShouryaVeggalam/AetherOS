"""Infrastructure Digital Twin simulator — clone → scenario → evaluate → diff.

Pipeline operates exclusively on immutable snapshots. Never modifies AWS,
Azure, GCP, Kubernetes, Docker, or Edge resources. No mutating cloud APIs.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.infra_twin.clone import clone_snapshot
from aetheros.infra_twin.diff import diff_snapshots
from aetheros.infra_twin.evaluator import evaluate
from aetheros.infra_twin.models import (
    InfrastructureDiff,
    InfrastructureSnapshot,
    SimulationResult,
    TwinScenario,
)
from aetheros.infra_twin.scenarios import apply_scenario, library
from aetheros.infra_twin.snapshot import demo_snapshot


@dataclass(frozen=True, slots=True)
class TwinRun:
    """Complete simulation artifact for one scenario."""

    baseline: InfrastructureSnapshot
    cloned: InfrastructureSnapshot
    after: InfrastructureSnapshot
    scenario: TwinScenario
    result: SimulationResult
    diff: InfrastructureDiff


class InfrastructureTwinSimulator:
    """Run explainable what-if simulations on cloned infrastructure twins."""

    def __init__(self, baseline: InfrastructureSnapshot | None = None) -> None:
        self._baseline = baseline or demo_snapshot()

    @property
    def baseline(self) -> InfrastructureSnapshot:
        """Live (immutable) baseline snapshot used for cloning."""

        return self._baseline

    def set_baseline(self, snapshot: InfrastructureSnapshot) -> None:
        """Replace the baseline reference (snapshot itself stays frozen)."""

        self._baseline = snapshot

    def scenarios(self) -> tuple[TwinScenario, ...]:
        """Return the built-in scenario library."""

        return library()

    def simulate(self, scenario: TwinScenario) -> TwinRun:
        """Execute Snapshot → Clone → Apply → Evaluate → Diff."""

        baseline = self._baseline
        cloned = clone_snapshot(baseline)
        # Guard: original baseline topology ids must remain untouched.
        after = apply_scenario(cloned, scenario)
        result = evaluate(after, scenario, baseline=baseline)
        delta = diff_snapshots(baseline, after)
        return TwinRun(
            baseline=baseline,
            cloned=cloned,
            after=after,
            scenario=scenario,
            result=result,
            diff=delta,
        )

    def simulate_kind(self, kind: str) -> TwinRun:
        """Simulate the first library scenario matching ``kind``."""

        token = kind.strip().upper().replace(" ", "_")
        for scenario in self.scenarios():
            if scenario.kind == token:
                return self.simulate(scenario)
        raise ValueError(f"no library scenario for kind: {kind}")
