"""Digital Twin evaluator — stability, bottleneck, risk, confidence.

Uses ResourceGraph structure and optional graph-reasoning signals.
No hardcoded recommendation strings beyond measurable templates.
"""

from __future__ import annotations

from aetheros.graph.queries import nodes_of_type
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.twin.models import (
    RiskLevel,
    SimulationResult,
    SimulationScenario,
    TwinSnapshot,
)


def evaluate(
    baseline: TwinSnapshot,
    simulated: TwinSnapshot,
    scenario: SimulationScenario,
) -> SimulationResult:
    """Evaluate a simulated twin against its baseline snapshot."""

    tel = simulated.telemetry
    base = baseline.telemetry
    predicted_cpu = tel.cpu_percent
    predicted_memory = tel.memory_percent
    predicted_disk = tel.disk_percent
    predicted_battery = tel.battery_percent

    utilization = _mean(
        predicted_cpu,
        predicted_memory,
        predicted_disk,
    )
    headroom = 100.0 - utilization
    process_shock = abs(base.process_count - tel.process_count)
    stability = _clamp(
        40.0
        + 0.45 * headroom
        - 0.25 * max(0.0, predicted_cpu - 85.0)
        - 0.20 * max(0.0, predicted_memory - 85.0)
        - 5.0 * process_shock
    )
    bottleneck = _bottleneck(tel)
    risk = _risk(predicted_cpu, predicted_memory, predicted_disk, predicted_battery)
    confidence = _confidence(baseline, simulated, scenario)
    reasoning = _reasoning(scenario, baseline, simulated, bottleneck, risk)
    return SimulationResult(
        predicted_cpu=predicted_cpu,
        predicted_memory=predicted_memory,
        predicted_disk=predicted_disk,
        predicted_battery=predicted_battery,
        stability=stability,
        confidence=confidence,
        reasoning=reasoning,
        risk=risk,
        bottleneck=bottleneck,
        scenario=scenario,
    )


def _bottleneck(tel: TelemetrySnapshot) -> str:
    """Resource with the highest predicted utilization."""

    candidates = {
        "cpu": tel.cpu_percent,
        "memory": tel.memory_percent,
        "disk": tel.disk_percent,
    }
    if tel.battery_percent is not None:
        # Low battery is inverted pressure.
        candidates["battery"] = 100.0 - tel.battery_percent
    return max(candidates, key=candidates.get)


def _risk(
    cpu: float,
    memory: float,
    disk: float,
    battery: float | None,
) -> RiskLevel:
    """Map peak pressure into a discrete risk level."""

    peak = max(cpu, memory, disk)
    if battery is not None and battery <= 15.0:
        peak = max(peak, 100.0 - battery)
    if peak >= 95.0:
        return "critical"
    if peak >= 85.0:
        return "high"
    if peak >= 70.0:
        return "medium"
    return "low"


def _confidence(
    baseline: TwinSnapshot,
    simulated: TwinSnapshot,
    scenario: SimulationScenario,
) -> float:
    """Confidence from graph completeness + scenario specificity."""

    graph = simulated.resource_graph
    node_score = min(1.0, len(graph.nodes) / 8.0)
    edge_score = min(1.0, len(graph.edges) / 8.0)
    process_score = min(1.0, len(nodes_of_type(graph, "Process")) / 3.0)
    mod_score = min(1.0, len(scenario.modifications) / 2.0)
    drift = (
        abs(simulated.telemetry.cpu_percent - baseline.telemetry.cpu_percent)
        + abs(simulated.telemetry.memory_percent - baseline.telemetry.memory_percent)
    ) / 200.0
    raw = (
        0.30 * node_score
        + 0.25 * edge_score
        + 0.20 * process_score
        + 0.15 * mod_score
        + 0.10 * min(1.0, drift)
    )
    return round(100.0 * max(0.0, min(1.0, raw)), 1)


def _reasoning(
    scenario: SimulationScenario,
    baseline: TwinSnapshot,
    simulated: TwinSnapshot,
    bottleneck: str,
    risk: RiskLevel,
) -> str:
    """Build an explanation from measurable deltas and graph facts."""

    base = baseline.telemetry
    sim = simulated.telemetry
    cpu_delta = sim.cpu_percent - base.cpu_percent
    mem_delta = sim.memory_percent - base.memory_percent
    processes = nodes_of_type(simulated.resource_graph, "Process")
    removed = baseline.telemetry.process_count - simulated.telemetry.process_count
    parts = [
        f"Scenario {scenario.name}: {scenario.description}",
        f"CPU {base.cpu_percent:.1f}% → {sim.cpu_percent:.1f}% ({cpu_delta:+.1f})",
        f"Memory {base.memory_percent:.1f}% → {sim.memory_percent:.1f}% ({mem_delta:+.1f})",
        f"Bottleneck={bottleneck}; risk={risk}; "
        f"process_nodes={len(processes)}; removed_processes={max(0, removed)}.",
    ]
    return " ".join(parts)


def _mean(*values: float) -> float:
    return sum(values) / len(values) if values else 0.0


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))
