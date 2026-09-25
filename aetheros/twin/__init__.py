"""Global Digital Twin + host Digital Twin 2.0 (P7).

* Global: ``TwinSimulator`` / ``GlobalTwin`` (Fabric-era worldwide what-ifs).
* Host Digital Twin 2.0: ResourceGraph snapshots, scenarios, evaluate, diff.
"""

from aetheros.twin.diff import diff_twins, format_metric_lines
from aetheros.twin.evaluator import evaluate
from aetheros.twin.formatter import DigitalTwinPanel
from aetheros.twin.global_twin import GlobalTwin, GlobalTwinReport
from aetheros.twin.models import (
    MetricChange,
    SimulationResult,
    SimulationScenario,
    SnapshotDiff,
    TwinSnapshot,
)
from aetheros.twin.planner import TwinPlan, TwinPlanner
from aetheros.twin.scenario import apply_scenario, builtin_scenario
from aetheros.twin.simulator import (
    SEED_SCENARIOS,
    DigitalTwinReport,
    DigitalTwinSimulator,
    TwinOutcome,
    TwinScenario,
    TwinSimulator,
)
from aetheros.twin.snapshot import clone_snapshot, create_snapshot, restore_snapshot

__all__ = [
    "SEED_SCENARIOS",
    "DigitalTwinPanel",
    "DigitalTwinReport",
    "DigitalTwinSimulator",
    "GlobalTwin",
    "GlobalTwinReport",
    "MetricChange",
    "SimulationResult",
    "SimulationScenario",
    "SnapshotDiff",
    "TwinOutcome",
    "TwinPlan",
    "TwinPlanner",
    "TwinScenario",
    "TwinSimulator",
    "TwinSnapshot",
    "apply_scenario",
    "builtin_scenario",
    "clone_snapshot",
    "create_snapshot",
    "diff_twins",
    "evaluate",
    "format_metric_lines",
    "restore_snapshot",
]
