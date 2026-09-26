"""Horizon Observatory snapshot — immutable presentation state.

Aggregates optional references to Cloud Federation, Topology, Global Graph,
Planetary Scheduler, Infrastructure Twin, Consensus, and Research models.
Never mutates them. Never runs engines.
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
class HorizonSnapshot:
    """Read-only bundle of global infrastructure presentation inputs.

    All fields are optional so Horizon can render idle states without live data.
    Values should be frozen models / tuples from existing packages.
    """

    generated_at: datetime | None = None
    # Cloud Federation (v6 P1)
    cloud_snapshot: Any = None
    cloud_health: Any = None
    cloud_records: tuple[Any, ...] = ()
    cloud_age_seconds: float = 0.0
    # Topology
    topology_graph: Any = None
    # Global Knowledge Graph (v6 P3)
    knowledge_graph: Any = None
    knowledge_evidence: Any = None
    knowledge_validation: Any = None
    # Planetary Scheduler (v6 P4)
    schedule_decision: Any = None
    schedule_workload: Any = None
    # Infrastructure Digital Twin (v6 P2)
    twin_run: Any = None
    twin_snapshot: Any = None
    twin_scenarios: tuple[Any, ...] = ()
    twin_scenario_name: str = ""
    # Consensus
    consensus_decision: Any = None
    consensus_findings: tuple[Any, ...] = ()
    consensus_conflicts: tuple[Any, ...] = ()
    # Research
    research_report: Any = None
    research_journal: tuple[Any, ...] = ()
    research_discoveries: tuple[Any, ...] = ()
    # Census / summary numbers (presentation only)
    global_health: float = 0.0
    connected_providers: int = 0
    regions: int = 0
    clusters: int = 0
    nodes: int = 0
    discoveries: int = 0
    active_simulations: int = 0
    consensus_confidence: float = 0.0
    health_signals: tuple[HealthSignal, ...] = ()
    timeline_events: tuple[tuple[str, str], ...] = ()

    def provider_count(self) -> int:
        """Connected provider count (presentation helper)."""

        return max(0, int(self.connected_providers))
