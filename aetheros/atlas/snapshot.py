"""AtlasSnapshot — immutable presentation state for the Atlas dashboard.

Aggregates optional references to existing federation / topology / scheduler /
consensus / twin / research models. Never mutates them. Never runs engines.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class HealthSignal:
    """One subsystem health indicator (green / yellow / red)."""

    name: str
    status: str  # green | yellow | red
    detail: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        if self.status not in {"green", "yellow", "red"}:
            raise ValueError("status must be green, yellow, or red")


@dataclass(frozen=True, slots=True)
class AtlasSnapshot:
    """Read-only bundle of distributed infrastructure presentation inputs.

    All fields are optional so Atlas can render idle states without live data.
    Values should be frozen models / tuples from existing packages.
    """

    generated_at: datetime | None = None
    # Federation
    federation_registry: Any = None  # RegistryView | None
    federation_heartbeats: tuple[Any, ...] = ()
    protocol_version: str = ""
    # Topology
    topology_graph: Any = None  # TopologyGraph | None
    # Scheduler
    schedule_result: Any = None  # ScheduleResult | None
    schedule_workload: Any = None  # Workload | None
    # Consensus
    consensus_decision: Any = None  # ConsensusDecision | None
    consensus_findings: tuple[Any, ...] = ()
    consensus_conflicts: tuple[Any, ...] = ()
    # Digital Twin
    twin_report: Any = None  # DigitalTwinReport | None
    twin_scenario_name: str = ""
    twin_baseline: Any = None  # TwinSnapshot | None
    # Research
    research_report: Any = None  # SystemResearchReport | None
    research_journal: tuple[Any, ...] = ()
    # Host telemetry summary (presentation numbers only)
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    connected_nodes: int = 0
    online_nodes: int = 0
    cluster_health: float = 0.0
    discoveries: int = 0
    active_simulations: int = 0
    health_signals: tuple[HealthSignal, ...] = ()

    def online_percent(self) -> float:
        if self.connected_nodes <= 0:
            return 0.0
        return round(100.0 * self.online_nodes / self.connected_nodes, 1)
