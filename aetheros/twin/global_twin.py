"""Global Digital Twin facade — worldwide scenario orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

from aetheros.twin.planner import TwinPlan, TwinPlanner
from aetheros.twin.simulator import SEED_SCENARIOS


@dataclass(frozen=True, slots=True)
class GlobalTwinReport:
    """Immutable global twin report for Fabric UI / API."""

    plan: TwinPlan
    scenario_count: int
    status: str = "Simulation Only"


@dataclass
class GlobalTwin:
    """Facade over twin planner for Fabric runtime."""

    planner: TwinPlanner = field(default_factory=TwinPlanner)
    last: GlobalTwinReport | None = field(default=None, init=False)

    def observe(self) -> GlobalTwinReport:
        """Run the default global twin plan."""

        plan = self.planner.plan(SEED_SCENARIOS)
        report = GlobalTwinReport(plan=plan, scenario_count=len(SEED_SCENARIOS))
        self.last = report
        return report
