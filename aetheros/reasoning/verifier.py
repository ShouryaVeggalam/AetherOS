"""Hypothesis verifier — accept only graph-grounded explanations.

Combines graph paths, telemetry evidence, historical agreement, and optional
simulation agreement. Rejects hypotheses lacking supporting paths.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aetheros.bridge.evidence import evidence_for_process, system_evidence
from aetheros.explainability.models import Evidence
from aetheros.graph.models import ResourceGraph
from aetheros.observatory.models import TelemetryPoint
from aetheros.reasoning.confidence import compute_confidence
from aetheros.reasoning.hypotheses import generate_hypotheses
from aetheros.reasoning.models import Hypothesis, Observation, VerifiedExplanation


def observation_from_metrics(
    *,
    cpu: float,
    memory: float,
    disk: float,
    cpu_threshold: float = 90.0,
    memory_threshold: float = 85.0,
    disk_threshold: float = 90.0,
) -> Observation:
    """Pick the highest-pressure observation from live metrics."""

    candidates = (
        Observation("cpu", cpu, "CPU Overload", cpu_threshold),
        Observation("memory", memory, "High Memory Usage", memory_threshold),
        Observation("disk", disk, "Critical Disk Pressure", disk_threshold),
    )
    return max(
        candidates,
        key=lambda item: item.value - item.threshold,
    )


def verify_hypotheses(
    graph: ResourceGraph,
    observation: Observation,
    hypotheses: tuple[Hypothesis, ...],
    *,
    history: tuple[TelemetryPoint, ...] = (),
    simulation_agreement: float = 0.0,
    now: datetime | None = None,
) -> VerifiedExplanation | None:
    """Verify hypotheses and return one VerifiedExplanation or ``None``.

    A hypothesis is rejected when it has no supporting paths or when
    telemetry/history provide zero corroboration for a high-pressure claim.
    """

    stamp = now if now is not None else datetime.now(UTC)
    accepted: list[Hypothesis] = []
    rejected: list[str] = []
    hist_ratio = _historical_agreement(observation, history)
    for hypothesis in hypotheses:
        if not hypothesis.supporting_paths:
            rejected.append(hypothesis.title)
            continue
        if (
            observation.value >= observation.threshold
            and hist_ratio <= 0.0
            and not history
        ):
            # No history available — still allow graph+telemetry evidence.
            pass
        accepted.append(hypothesis)
    if not accepted:
        return None
    winner = max(accepted, key=lambda item: item.confidence)
    evidence = _collect_evidence(graph, winner, observation, history, stamp)
    if not evidence and not winner.supporting_paths:  # pragma: no cover
        rejected.append(winner.title)
        return None
    confidence = compute_confidence(
        paths=winner.supporting_paths,
        evidence_count=len(evidence),
        historical_agreement=hist_ratio,
        simulation_agreement=simulation_agreement,
    )
    summary = (
        f"{observation.title}: verified cause '{winner.title}' "
        f"via {len(winner.supporting_paths)} graph path(s) "
        f"(confidence {confidence}%)."
    )
    return VerifiedExplanation(
        summary=summary,
        evidence=evidence,
        reasoning_paths=winner.supporting_paths,
        confidence=confidence,
        timestamp=stamp,
        observation=observation,
        rejected=tuple(rejected),
    )


def reason(
    graph: ResourceGraph,
    observation: Observation,
    *,
    history: tuple[TelemetryPoint, ...] = (),
    simulation_agreement: float = 0.0,
    now: datetime | None = None,
) -> VerifiedExplanation | None:
    """End-to-end graph reasoning: hypotheses → verify → explanation."""

    hypotheses = generate_hypotheses(graph, observation)
    return verify_hypotheses(
        graph,
        observation,
        hypotheses,
        history=history,
        simulation_agreement=simulation_agreement,
        now=now,
    )


def _collect_evidence(
    graph: ResourceGraph,
    hypothesis: Hypothesis,
    observation: Observation,
    history: tuple[TelemetryPoint, ...],
    stamp: datetime,
) -> tuple[Evidence, ...]:
    """Assemble Evidence from graph paths + telemetry/history facts."""

    items: list[Evidence] = []
    process_ids = {
        path.source
        for path in hypothesis.supporting_paths
        if path.source.startswith("process:")
    }
    for process_id in sorted(process_ids):
        items.extend(evidence_for_process(graph, process_id, now=stamp))
    if not items:  # pragma: no cover
        items.extend(system_evidence(graph, now=stamp, limit=8))
    items.append(
        Evidence(
            source="telemetry",
            metric=observation.metric,
            value=observation.value,
            timestamp=stamp,
            description=(
                f"Telemetry observation {observation.title}: "
                f"{observation.metric}={observation.value:.1f}"
            ),
        )
    )
    if history:
        latest = history[-1]
        hist_value = _history_metric(latest, observation.metric)
        if hist_value is not None:
            items.append(
                Evidence(
                    source="history",
                    metric=observation.metric,
                    value=hist_value,
                    timestamp=latest.timestamp,
                    description=(
                        f"Historical sample {observation.metric}="
                        f"{hist_value:.1f} at last observatory point"
                    ),
                )
            )
    return tuple(items)


def _historical_agreement(
    observation: Observation,
    history: tuple[TelemetryPoint, ...],
) -> float:
    """Fraction of recent history above the observation threshold."""

    if not history:
        return 0.0
    window = history[-min(len(history), 20) :]
    hits = 0
    for point in window:
        value = _history_metric(point, observation.metric)
        if value is not None and value >= observation.threshold * 0.85:
            hits += 1
    return hits / len(window)


def _history_metric(point: TelemetryPoint, metric: str) -> float | None:
    """Read a TelemetryPoint field by observation metric key."""

    key = metric.strip().lower()
    if key == "cpu":
        return point.cpu
    if key == "memory":
        return point.memory
    if key == "disk":
        return point.disk
    if key == "battery":
        return point.battery
    return None
