"""Node scoring engine — weighted normalized scores in [0, 100].

No hardcoded winners. Deterministic function of capacity, latency, health,
and utilization relative to the workload request.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.scheduler.models import NodeCapacity, Workload


@dataclass(frozen=True, slots=True)
class ScoreWeights:
    """Relative weights for scoring dimensions (need not sum to 1)."""

    cpu: float = 0.25
    memory: float = 0.20
    gpu: float = 0.15
    latency: float = 0.15
    cluster_health: float = 0.15
    utilization: float = 0.10

    def __post_init__(self) -> None:
        total = (
            self.cpu
            + self.memory
            + self.gpu
            + self.latency
            + self.cluster_health
            + self.utilization
        )
        if total <= 0:
            raise ValueError("weights must sum to a positive value")


DEFAULT_WEIGHTS = ScoreWeights()


def score_node(
    workload: Workload,
    node: NodeCapacity,
    *,
    weights: ScoreWeights | None = None,
) -> tuple[float, str]:
    """Return ``(score 0–100, reasoning)`` for one candidate node."""

    w = weights or DEFAULT_WEIGHTS
    cpu_s = _availability(node.available_cpu, workload.cpu_request)
    mem_s = _availability(node.available_memory, workload.memory_request)
    gpu_s = (
        _availability(node.available_gpu, max(workload.gpu_request, 0.01))
        if workload.gpu_request > 0
        else _availability(node.available_gpu, 0.0)
    )
    latency_s = _latency_score(node.latency_ms)
    health_s = max(0.0, min(100.0, node.cluster_health))
    util_s = max(0.0, min(100.0, 100.0 - node.utilization))

    # Priority gently boosts preference for healthier headroom.
    priority_boost = 1.0 + (workload.priority / 100.0) * 0.05

    raw = (
        w.cpu * cpu_s
        + w.memory * mem_s
        + w.gpu * gpu_s
        + w.latency * latency_s
        + w.cluster_health * health_s
        + w.utilization * util_s
    )
    denom = w.cpu + w.memory + w.gpu + w.latency + w.cluster_health + w.utilization
    score = round(min(100.0, (raw / denom) * priority_boost), 2)
    reasoning = (
        f"cpu={cpu_s:.0f} mem={mem_s:.0f} gpu={gpu_s:.0f} "
        f"lat={latency_s:.0f} health={health_s:.0f} util_headroom={util_s:.0f} "
        f"→ {score:.1f}"
    )
    return score, reasoning


def _availability(available: float, request: float) -> float:
    """Higher remaining headroom after request → higher score."""

    if request <= 0:
        return max(0.0, min(100.0, available))
    if available + 1e-9 < request:
        return 0.0
    remaining = available - request
    # Full score when remaining capacity is plentiful.
    return max(0.0, min(100.0, remaining))


def _latency_score(latency_ms: float) -> float:
    """Map latency to 0–100 (lower latency → higher score)."""

    # 0 ms → 100, 50 ms → ~0, clamped.
    return max(0.0, min(100.0, 100.0 - latency_ms * 2.0))
