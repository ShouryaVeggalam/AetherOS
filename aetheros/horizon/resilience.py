"""Resilience Simulator — what-if planetary failure scenarios.

Simulation only. Never triggers failovers, never contacts hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from aetheros.horizon.world_graph import WorldGraph

FailureKind = Literal[
    "region_outage",
    "datacenter_failure",
    "network_partition",
    "power_loss",
]


@dataclass(frozen=True, slots=True)
class FailureScenario:
    """One immutable failure hypothesis.

    Attributes:
        kind: Failure class.
        target_id: Topology id affected (region, dc, …).
        capacity_loss_pct: Assumed capacity removed (0–100).
        description: Public systems narrative.
    """

    kind: FailureKind
    target_id: str
    capacity_loss_pct: float
    description: str

    def __post_init__(self) -> None:
        """Validate loss percentage."""

        if not 0.0 <= self.capacity_loss_pct <= 100.0:
            raise ValueError("capacity_loss_pct must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class ResilienceReport:
    """Outcome of a resilience simulation.

    Attributes:
        scenario: Input failure hypothesis.
        remaining_capacity_pct: Planetary capacity still available.
        cluster_health: Estimated mean cluster health 0–100.
        global_stability: Composite stability score 0–100.
        world_health_after: Projected world health 0–100.
        affected_nodes: Sample node ids marked impacted.
        explanation: Research-quality narrative.
        confidence: Model confidence 0–1.
    """

    scenario: FailureScenario
    remaining_capacity_pct: float
    cluster_health: float
    global_stability: float
    world_health_after: float
    affected_nodes: tuple[str, ...]
    explanation: str
    confidence: float


@dataclass
class ResilienceSimulator:
    """Run read-only failure simulations against the world graph."""

    def simulate(
        self, graph: WorldGraph, scenario: FailureScenario
    ) -> ResilienceReport:
        """Project remaining capacity and health after ``scenario``."""

        census = graph.census
        base_health = census.world_health
        loss = scenario.capacity_loss_pct

        affected = _collect_affected(graph, scenario)
        # Scale sample impact into census-aware remaining capacity.
        remaining = max(0.0, 100.0 - loss)
        # Cluster health drops proportional to loss with damping.
        cluster_health = max(0.0, 100.0 - loss * 0.85)
        # Stability blends remaining capacity and sample graph health.
        sample_health = graph.average_health() * 100.0
        global_stability = max(
            0.0,
            0.55 * remaining + 0.25 * cluster_health + 0.2 * sample_health,
        )
        world_after = max(0.0, base_health - loss * 0.09)
        confidence = 0.82 if affected else 0.7
        explanation = (
            f"Simulated {scenario.kind.replace('_', ' ')} on {scenario.target_id}: "
            f"{scenario.description} Assumed capacity loss {loss:.1f}%. "
            f"Projected remaining capacity {remaining:.1f}%, "
            f"cluster health {cluster_health:.1f}%, "
            f"global stability {global_stability:.1f}%, "
            f"world health {base_health:.1f}% → {world_after:.1f}%. "
            "Simulation only — no remediation executed."
        )
        return ResilienceReport(
            scenario=scenario,
            remaining_capacity_pct=round(remaining, 2),
            cluster_health=round(cluster_health, 2),
            global_stability=round(global_stability, 2),
            world_health_after=round(world_after, 2),
            affected_nodes=affected,
            explanation=explanation,
            confidence=confidence,
        )

    def europe_capacity_loss(
        self,
        graph: WorldGraph,
        *,
        loss_pct: float = 15.0,
    ) -> ResilienceReport:
        """Convenience scenario: Europe loses ``loss_pct`` capacity."""

        return self.simulate(
            graph,
            FailureScenario(
                kind="region_outage",
                target_id="region.eu",
                capacity_loss_pct=loss_pct,
                description=f"Europe loses {loss_pct:.0f}% capacity.",
            ),
        )


def _collect_affected(graph: WorldGraph, scenario: FailureScenario) -> tuple[str, ...]:
    """List sample node ids under the failure target."""

    target = scenario.target_id
    if graph.node(target) is None:
        # Fuzzy match by region name substring.
        hits = [
            n.node_id
            for n in graph.nodes()
            if target.split(".")[-1].lower() in n.node_id.lower()
        ]
        return tuple(hits[:24])
    affected = [target]
    for _, node in graph.iter_hierarchy(target):
        if node.node_id != target:
            affected.append(node.node_id)
    return tuple(affected[:48])
