"""Deterministic evaluator for infrastructure twin simulations.

Computes availability, stability, latency, utilization, risk, and confidence.
Pure functions over immutable snapshots — no cloud I/O.
"""

from __future__ import annotations

from aetheros.infra_twin.models import (
    InfrastructureSnapshot,
    RiskLevel,
    SimulationResult,
    TwinScenario,
)


def mean_load(snapshot: InfrastructureSnapshot) -> float:
    """Average load across available nodes (0 if none)."""

    alive = [n for n in snapshot.topology if n.available]
    if not alive:
        return 100.0
    return sum(n.load for n in alive) / len(alive)


def mean_latency(snapshot: InfrastructureSnapshot) -> float:
    """Average latency_ms across available nodes (penalize total outage)."""

    alive = [n for n in snapshot.topology if n.available]
    if not alive:
        return 999.0
    return sum(n.latency_ms for n in alive) / len(alive)


def availability_pct(snapshot: InfrastructureSnapshot) -> float:
    """Percent of topology nodes still available."""

    total = len(snapshot.topology)
    if total == 0:
        return 0.0
    return 100.0 * snapshot.available_nodes / total


def stability_score(snapshot: InfrastructureSnapshot) -> float:
    """Cluster stability 0–100 from availability and load headroom."""

    avail = availability_pct(snapshot)
    load = mean_load(snapshot)
    headroom = max(0.0, 100.0 - load)
    return max(0.0, min(100.0, 0.65 * avail + 0.35 * headroom))


def risk_level(availability: float, latency: float, load: float) -> RiskLevel:
    """Map metrics to a discrete risk label (deterministic)."""

    if availability < 50.0 or load >= 95.0:
        return "critical"
    if availability < 85.0 or latency >= 40.0 or load >= 85.0:
        return "high"
    if availability < 97.0 or latency >= 15.0 or load >= 70.0:
        return "medium"
    return "low"


def confidence_score(
    snapshot: InfrastructureSnapshot,
    *,
    baseline_nodes: int,
) -> float:
    """Confidence rises with census size and falls when topology empties."""

    n = len(snapshot.topology)
    if n == 0:
        return 40.0
    size_factor = min(1.0, n / max(1, baseline_nodes or n))
    avail = availability_pct(snapshot) / 100.0
    return max(40.0, min(99.0, 70.0 + 20.0 * size_factor + 9.0 * avail))


def evaluate(
    snapshot: InfrastructureSnapshot,
    scenario: TwinScenario,
    *,
    baseline: InfrastructureSnapshot | None = None,
) -> SimulationResult:
    """Evaluate a (post-scenario) twin snapshot into a SimulationResult."""

    cpu = mean_load(snapshot)  # proxy utilization
    memory = min(100.0, cpu * 0.92 + 4.0)
    latency = mean_latency(snapshot)
    availability = availability_pct(snapshot)
    stability = stability_score(snapshot)
    baseline_nodes = (
        baseline.node_count if baseline is not None else snapshot.node_count
    )
    confidence = confidence_score(snapshot, baseline_nodes=baseline_nodes)
    risk = risk_level(availability, latency, cpu)
    affected = 0
    if baseline is not None:
        before = {n.id: n for n in baseline.topology}
        for node in snapshot.topology:
            prev = before.get(node.id)
            if prev is not None and prev.available and not node.available:
                affected += 1
    explanation = (
        f"Scenario {scenario.kind}: availability {availability:.2f}%, "
        f"latency {latency:.1f} ms, stability {stability:.1f}, "
        f"affected nodes {affected}. Simulation only — no live mutations."
    )
    return SimulationResult(
        cpu=round(cpu, 2),
        memory=round(memory, 2),
        latency=round(latency, 2),
        availability=round(availability, 2),
        stability=round(stability, 2),
        confidence=round(confidence, 2),
        risk=risk,
        explanation=explanation,
        scenario_id=scenario.id,
    )
