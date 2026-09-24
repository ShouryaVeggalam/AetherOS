"""Suitability scoring for orchestrator candidates.

Weighted scores from availability metrics. Recommendation-only.
"""

from __future__ import annotations

from aetheros.orchestrator.models import (
    CandidateNode,
    DemandLevel,
    NodeScore,
    WorkloadProfile,
)

_DEMAND_WEIGHT: dict[DemandLevel, float] = {
    "high": 1.0,
    "medium": 0.6,
    "low": 0.3,
    "none": 0.0,
}


def score_node(node: CandidateNode, workload: WorkloadProfile) -> NodeScore:
    """Compute a 0–100 suitability score for one eligible node.

    Args:
        node: Candidate that already passed constraints.
        workload: Target workload profile.

    Returns:
        Immutable NodeScore with breakdown lines.
    """

    cpu_avail = 100.0 - node.cpu
    mem_avail = 100.0 - node.memory
    disk_avail = 100.0 - node.disk
    gpu_avail = max(0.0, min(100.0, node.gpu))
    battery_score = _battery_score(node)
    latency_score = _latency_score(node.network_latency)

    weights = {
        "cpu": _DEMAND_WEIGHT[workload.cpu],
        "memory": _DEMAND_WEIGHT[workload.memory],
        "disk": _DEMAND_WEIGHT[workload.disk],
        "gpu": _DEMAND_WEIGHT[workload.gpu],
        "battery": 0.25 if _DEMAND_WEIGHT[workload.cpu] > 0 else 0.1,
        "latency": _DEMAND_WEIGHT[workload.latency],
    }
    values = {
        "cpu": cpu_avail,
        "memory": mem_avail,
        "disk": disk_avail,
        "gpu": gpu_avail,
        "battery": battery_score,
        "latency": latency_score,
    }
    weight_sum = sum(weights.values()) or 1.0
    raw = sum(values[key] * weights[key] for key in weights) / weight_sum
    score = int(max(0, min(100, round(raw))))
    breakdown = _breakdown(node, values, weights)
    return NodeScore(node=node, score=score, breakdown=breakdown)


def score_nodes(
    nodes: tuple[CandidateNode, ...] | list[CandidateNode],
    workload: WorkloadProfile,
) -> tuple[NodeScore, ...]:
    """Score many nodes and return them ranked best-first."""

    ranked = [score_node(node, workload) for node in nodes]
    ranked.sort(key=lambda item: (-item.score, item.node.hostname.lower()))
    return tuple(ranked)


def _battery_score(node: CandidateNode) -> float:
    """Map battery / AC power into a 0–100 score."""

    if node.battery is None:
        return 95.0  # desktops / cloud assumed on AC
    return max(0.0, min(100.0, node.battery))


def _latency_score(latency_ms: float) -> float:
    """Lower latency → higher score (soft decay)."""

    # 0ms → 100, 50ms → ~50, 100ms+ → low
    return max(0.0, min(100.0, 100.0 - float(latency_ms)))


def _breakdown(
    node: CandidateNode,
    values: dict[str, float],
    weights: dict[str, float],
) -> tuple[str, ...]:
    """Build short evidence lines for explainability."""

    catalog = {
        "cpu": f"CPU availability {values['cpu']:.0f}% (load {node.cpu:.0f}%)",
        "memory": (
            f"Memory availability {values['memory']:.0f}% " f"(used {node.memory:.0f}%)"
        ),
        "disk": f"Disk availability {values['disk']:.0f}%",
        "gpu": f"GPU availability {values['gpu']:.0f}",
        "battery": f"Battery/power score {values['battery']:.0f}",
        "latency": (
            f"Latency score {values['latency']:.0f} " f"({node.network_latency:.1f} ms)"
        ),
    }
    ordered = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)
    lines = [catalog[key] for key, weight in ordered if weight > 0]
    return tuple(lines[:5])
