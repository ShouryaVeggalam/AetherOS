"""Confidence engine — score explanation trust from evidence quality.

Scores are derived from measurable inputs. Missing factors contribute
zero rather than inventing a default confidence.
"""

from __future__ import annotations

from aetheros.explainability.evidence import EvidenceBundle
from aetheros.explainability.models import Evidence
from aetheros.simulation.models import SimulationResult


def compute_confidence(
    bundle: EvidenceBundle,
    *,
    simulation: SimulationResult | None = None,
    current_cpu: float | None = None,
) -> int:
    """Compute a 0–100 confidence from evidence quality signals.

    Args:
        bundle: Collected evidence and quality metadata.
        simulation: Optional simulation used for agreement scoring.
        current_cpu: Live CPU for simulation agreement comparison.

    Returns:
        Integer confidence in [0, 100].
    """

    telemetry_q = _telemetry_quality(bundle.items)
    history_q = _history_quality(bundle.sample_count)
    sim_q = 0.0
    if bundle.has_simulation and simulation is not None:
        sim_q = _simulation_agreement(simulation, current_cpu)
    intent_q = float(max(0, min(100, bundle.intent_certainty)))

    score = telemetry_q * 0.30 + history_q * 0.25 + sim_q * 0.25 + intent_q * 0.20
    return int(max(0, min(100, round(score))))


def _telemetry_quality(items: tuple[Evidence, ...]) -> float:
    """Score completeness of live telemetry evidence."""

    metrics = {e.metric for e in items if e.source == "telemetry"}
    required = {"cpu", "memory", "disk"}
    present = len(required & metrics)
    if present == 0:
        return 0.0
    base = (present / len(required)) * 80.0
    if "battery" in metrics:
        base += 10.0
    if "process_cpu" in metrics:
        base += 10.0
    return min(100.0, base)


def _history_quality(sample_count: int) -> float:
    """Map history length to quality (more samples → higher trust)."""

    if sample_count <= 0:
        return 0.0
    return min(100.0, (sample_count / 300.0) * 100.0)


def _simulation_agreement(
    simulation: SimulationResult,
    current_cpu: float | None,
) -> float:
    """Score how well simulation support aligns with observed load."""

    score = simulation.stability_score * 0.5 + simulation.overall_improvement * 0.3
    if current_cpu is not None:
        relief = max(0.0, current_cpu - simulation.projected_cpu_percent)
        score += min(20.0, relief * 0.5)
    return min(100.0, score)
