"""Planetary scoring engine — weighted normalized scores in [0, 100].

Metrics: CPU capacity · memory availability · GPU availability · network
latency · cluster health · energy efficiency · regional resilience.

No hardcoded winners. Deterministic function of site census + workload.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.planetary.models import GlobalWorkload, PlacementSite


@dataclass(frozen=True, slots=True)
class ScoreWeights:
    """Relative weights for scoring dimensions (need not sum to 1)."""

    cpu: float = 0.18
    memory: float = 0.15
    gpu: float = 0.12
    latency: float = 0.18
    cluster_health: float = 0.12
    energy_efficiency: float = 0.12
    regional_resilience: float = 0.13

    def __post_init__(self) -> None:
        total = (
            self.cpu
            + self.memory
            + self.gpu
            + self.latency
            + self.cluster_health
            + self.energy_efficiency
            + self.regional_resilience
        )
        if total <= 0:
            raise ValueError("weights must sum to a positive value")


DEFAULT_WEIGHTS = ScoreWeights()


def score_site(
    workload: GlobalWorkload,
    site: PlacementSite,
    *,
    weights: ScoreWeights | None = None,
) -> tuple[float, str]:
    """Return ``(score 0–100, reasoning)`` for one planetary placement site."""

    w = weights or DEFAULT_WEIGHTS
    cpu_s = _availability(site.cpu_available, workload.cpu)
    mem_s = _availability(site.memory_available, workload.memory)
    gpu_s = (
        _availability(site.gpu_available, max(workload.gpu, 0.01))
        if workload.gpu > 0
        else _availability(site.gpu_available, 0.0)
    )
    latency_s = _latency_score(site.latency_ms, workload.latency_target)
    health_s = max(0.0, min(100.0, site.cluster_health))
    energy_s = max(0.0, min(100.0, site.energy_efficiency))
    resilience_s = max(0.0, min(100.0, site.regional_resilience))

    # Gentle preference boost when region matches soft preference.
    pref = workload.region_preference.strip().lower()
    pref_boost = 1.0
    if pref and site.region.strip().lower() == pref:
        pref_boost = 1.04

    raw = (
        w.cpu * cpu_s
        + w.memory * mem_s
        + w.gpu * gpu_s
        + w.latency * latency_s
        + w.cluster_health * health_s
        + w.energy_efficiency * energy_s
        + w.regional_resilience * resilience_s
    )
    denom = (
        w.cpu
        + w.memory
        + w.gpu
        + w.latency
        + w.cluster_health
        + w.energy_efficiency
        + w.regional_resilience
    )
    score = round(min(100.0, (raw / denom) * pref_boost), 2)
    reasoning = (
        f"cpu={cpu_s:.0f} mem={mem_s:.0f} gpu={gpu_s:.0f} "
        f"lat={latency_s:.0f} health={health_s:.0f} "
        f"energy={energy_s:.0f} resilience={resilience_s:.0f} "
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
    return max(0.0, min(100.0, remaining))


def _latency_score(latency_ms: float, target_ms: float) -> float:
    """Map latency to 0–100 relative to the workload latency target."""

    target = max(1.0, target_ms)
    # At target → ~50; well under → closer to 100; far over → near 0.
    ratio = latency_ms / target
    return max(0.0, min(100.0, 100.0 - ratio * 50.0))
