"""Horizon runtime — assemble a planetary intelligence report.

Wires world graph, latency, resilience, and capacity into one
immutable report for the dashboard and API.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aetheros.horizon.capacity import CapacityPlan, CapacityPlanner
from aetheros.horizon.latency import LatencyEngine, LatencyEstimate
from aetheros.horizon.resilience import ResilienceReport, ResilienceSimulator
from aetheros.horizon.world_graph import WorldGraph, WorldGraphSnapshot


@dataclass(frozen=True, slots=True)
class HorizonReport:
    """Immutable Horizon planetary intelligence snapshot."""

    world: WorldGraphSnapshot
    latency: tuple[LatencyEstimate, ...]
    resilience: ResilienceReport
    capacity: CapacityPlan
    status: str = "Read-only Planetary Intelligence"

    @property
    def world_health(self) -> float:
        """Census world health percent."""

        return self.world.world_health

    @property
    def simulated_health(self) -> float:
        """World health after the active resilience scenario."""

        return self.resilience.world_health_after


@dataclass
class HorizonRuntime:
    """Run one Horizon observation cycle (simulation-first)."""

    graph: WorldGraph = field(default_factory=WorldGraph)
    latency_engine: LatencyEngine = field(default_factory=LatencyEngine)
    resilience: ResilienceSimulator = field(default_factory=ResilienceSimulator)
    capacity_planner: CapacityPlanner = field(default_factory=CapacityPlanner)
    last: HorizonReport | None = field(default=None, init=False)

    def observe(self, *, europe_loss_pct: float = 15.0) -> HorizonReport:
        """Build a full Horizon report with a default Europe what-if."""

        latency = self.latency_engine.estimate_regions(self.graph)
        resilience = self.resilience.europe_capacity_loss(
            self.graph, loss_pct=europe_loss_pct
        )
        capacity = self.capacity_planner.plan(self.graph)
        report = HorizonReport(
            world=self.graph.snapshot(),
            latency=latency,
            resilience=resilience,
            capacity=capacity,
        )
        self.last = report
        return report
