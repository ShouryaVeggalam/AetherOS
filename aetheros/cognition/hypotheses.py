"""Hypothesis engine — generate candidate explanations for anomalies.

Abductive candidates with evidence-weighted probabilities.
Never executes interventions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from aetheros.cognition.memory import CognitiveFact, CognitiveMemory
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot


@dataclass(frozen=True, slots=True)
class Observation:
    """Immutable observation that triggers hypothesis generation."""

    kind: str
    summary: str
    metric: str
    value: float
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """One candidate causal explanation.

    Attributes:
        hypothesis_id: Stable id.
        title: Short label.
        description: Public systems explanation.
        probability: 0.0–1.0 prior / posterior belief.
        evidence: Supporting evidence lines.
        related_process: Optional process/pattern name.
    """

    hypothesis_id: str
    title: str
    description: str
    probability: float
    evidence: tuple[str, ...]
    related_process: str | None = None

    def __post_init__(self) -> None:
        """Validate probability."""

        if not 0.0 <= self.probability <= 1.0:
            raise ValueError("probability must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class HypothesisSet:
    """Ranked hypotheses for one observation."""

    observation: Observation
    hypotheses: tuple[Hypothesis, ...]


def observe_from_snapshot(
    snapshot: TelemetrySnapshot,
    *,
    cpu_critical: float = 90.0,
) -> Observation | None:
    """Build an Observation from telemetry when an anomaly is present."""

    if snapshot.cpu_percent >= cpu_critical:
        return Observation(
            kind="cpu_pressure",
            summary=f"CPU reached {snapshot.cpu_percent:.0f}%.",
            metric="cpu",
            value=snapshot.cpu_percent,
            timestamp=snapshot.timestamp,
        )
    if snapshot.memory_percent >= 90.0:
        return Observation(
            kind="memory_pressure",
            summary=f"Memory reached {snapshot.memory_percent:.0f}%.",
            metric="memory",
            value=snapshot.memory_percent,
            timestamp=snapshot.timestamp,
        )
    if snapshot.disk_percent >= 90.0:
        return Observation(
            kind="disk_pressure",
            summary=f"Disk reached {snapshot.disk_percent:.0f}%.",
            metric="disk",
            value=snapshot.disk_percent,
            timestamp=snapshot.timestamp,
        )
    return None


def generate_hypotheses(
    observation: Observation,
    *,
    memory: CognitiveMemory | None = None,
    history: tuple[TelemetryPoint, ...] = (),
    top_processes: tuple[str, ...] = (),
) -> HypothesisSet:
    """Generate ranked hypotheses for an observation.

    Probabilities are evidence-weighted heuristics — not learned ML models.
    """

    facts = memory.list_facts() if memory is not None else ()
    candidates: list[Hypothesis] = []

    candidates.append(
        _hyp_process(
            "cursor_compile",
            "Cursor compilation",
            "IDE compile / language-server work elevated CPU.",
            observation,
            top_processes,
            facts,
            keys=("cursor", "code", "python"),
            base=0.35,
        )
    )
    candidates.append(
        _hyp_process(
            "background_indexing",
            "Background indexing",
            "Background indexing caused sustained load.",
            observation,
            top_processes,
            facts,
            keys=("index", "mds", "spotlight", "rg"),
            base=0.3,
        )
    )
    candidates.append(
        _hyp_process(
            "browser_rendering",
            "Browser rendering",
            "Browser compositor / renderer threads spiked CPU.",
            observation,
            top_processes,
            facts,
            keys=("chrome", "safari", "firefox", "browser"),
            base=0.25,
        )
    )
    candidates.append(
        Hypothesis(
            hypothesis_id="simulation_workload",
            title="Simulation workload",
            description="Research/simulation scoring contended for CPU (userspace only).",
            probability=_clamp(
                0.15 + (0.1 if observation.kind == "cpu_pressure" else 0.0)
            ),
            evidence=(
                observation.summary,
                "Simulation engine is pure math — listed as a candidate actor only.",
            ),
            related_process="simulation",
        )
    )

    if history:
        streak = _high_streak_seconds(history, observation.metric, 90.0)
        if streak >= 60:
            for index, hyp in enumerate(list(candidates)):
                bump = (
                    0.05
                    if "sustained" in hyp.description.lower()
                    or "index" in hyp.hypothesis_id
                    else 0.02
                )
                candidates[index] = Hypothesis(
                    hypothesis_id=hyp.hypothesis_id,
                    title=hyp.title,
                    description=hyp.description,
                    probability=_clamp(hyp.probability + bump),
                    evidence=hyp.evidence
                    + (f"Metric stayed elevated ~{streak}s in history.",),
                    related_process=hyp.related_process,
                )

    ranked = tuple(sorted(candidates, key=lambda h: (-h.probability, h.title.lower())))
    ranked = _normalize(ranked)
    return HypothesisSet(observation=observation, hypotheses=ranked)


def _hyp_process(
    hyp_id: str,
    title: str,
    description: str,
    observation: Observation,
    top_processes: tuple[str, ...],
    facts: tuple[CognitiveFact, ...],
    *,
    keys: tuple[str, ...],
    base: float,
) -> Hypothesis:
    """Build a process-pattern hypothesis with evidence bumps."""

    evidence = [observation.summary]
    score = base
    matched = _match_process(top_processes, keys)
    if matched:
        score += 0.25
        evidence.append(f"Top process match: {matched}.")
    for fact in facts:
        if any(k in fact.subject.lower() or k in fact.notes.lower() for k in keys):
            score += 0.1 * fact.confidence
            evidence.append(fact.notes)
            break
    return Hypothesis(
        hypothesis_id=hyp_id,
        title=title,
        description=description,
        probability=_clamp(score),
        evidence=tuple(evidence),
        related_process=matched,
    )


def _match_process(processes: tuple[str, ...], keys: tuple[str, ...]) -> str | None:
    """Return first process name matching any key."""

    for name in processes:
        lower = name.lower()
        if any(k in lower for k in keys):
            return name
    return None


def _high_streak_seconds(
    history: tuple[TelemetryPoint, ...],
    metric: str,
    threshold: float,
) -> int:
    """Count trailing seconds above threshold for a metric."""

    if len(history) < 2:
        return 0
    streak_points = 0
    for point in reversed(history):
        value = getattr(point, metric, None)
        if value is None or float(value) < threshold:
            break
        streak_points += 1
    if streak_points < 2:
        return 0
    first = history[-streak_points].timestamp
    last = history[-1].timestamp
    return max(0, int((last - first).total_seconds()))


def _normalize(hypotheses: tuple[Hypothesis, ...]) -> tuple[Hypothesis, ...]:
    """Renormalize probabilities to sum ≈ 1 while preserving rank."""

    total = sum(h.probability for h in hypotheses) or 1.0
    return tuple(
        Hypothesis(
            hypothesis_id=h.hypothesis_id,
            title=h.title,
            description=h.description,
            probability=_clamp(h.probability / total),
            evidence=h.evidence,
            related_process=h.related_process,
        )
        for h in hypotheses
    )


def _clamp(value: float) -> float:
    """Clamp probability into [0, 1]."""

    return max(0.0, min(1.0, round(value, 4)))


def utc_now() -> datetime:
    """Timezone-aware UTC now."""

    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# v3 Cognition Core — evidence → Core Hypothesis (models.Hypothesis)
# ---------------------------------------------------------------------------


def generate_core_hypotheses(
    evidence: tuple,
    *,
    context_label: str = "BALANCED",
    patterns: tuple[str, ...] = (),
) -> tuple:
    """Build v3 ``models.Hypothesis`` candidates from evidence only.

    Returns an empty tuple when evidence is insufficient. Never invents
    unsupported explanations. Does not alter legacy ``Hypothesis`` generation.
    """

    from aetheros.cognition.models import Hypothesis as CoreHypothesis

    if not evidence:
        return ()

    by_source: dict[str, list] = {}
    for item in evidence:
        by_source.setdefault(item.source, []).append(item)

    hypotheses: list[CoreHypothesis] = []
    graph_items = by_source.get("resource_graph", [])
    hist_items = by_source.get("telemetry_history", [])
    twin_items = by_source.get("digital_twin", [])
    mem_items = by_source.get("operational_memory", [])

    cpu_paths = [
        e
        for e in graph_items
        if e.metric.startswith("path:") and "cpu" in e.metric.lower()
    ]
    proc_cpu = [e for e in graph_items if e.metric.startswith("process_cpu:")]
    if proc_cpu or cpu_paths:
        top = max(proc_cpu or graph_items, key=lambda e: abs(e.value))
        support = tuple(e.id for e in (proc_cpu or graph_items)[:5])
        if cpu_paths:
            support = support + tuple(e.id for e in cpu_paths[:3])
        hypotheses.append(
            CoreHypothesis(
                id=f"hyp_cpu_{top.id[-8:]}",
                title=f"{context_label} foreground CPU pressure",
                description=(
                    f"Graph evidence shows elevated process/CPU coupling "
                    f"(peak metric value {top.value:.1f})."
                ),
                supporting_evidence=support,
                confidence=min(95.0, 55.0 + min(40.0, abs(top.value) * 0.4)),
            )
        )

    cpu_delta = next((e for e in hist_items if e.metric == "cpu_delta"), None)
    if cpu_delta is not None and abs(cpu_delta.value) >= 5.0:
        direction = "increase" if cpu_delta.value > 0 else "decrease"
        support = tuple(e.id for e in hist_items)
        hypotheses.append(
            CoreHypothesis(
                id=f"hyp_hist_{cpu_delta.id[-8:]}",
                title=f"Historical CPU {direction} under {context_label}",
                description=(
                    f"Telemetry history shows CPU delta {cpu_delta.value:+.1f} "
                    f"across recorded samples."
                ),
                supporting_evidence=support,
                confidence=min(92.0, 50.0 + abs(cpu_delta.value)),
            )
        )

    if twin_items and (proc_cpu or cpu_delta is not None):
        support = tuple(e.id for e in twin_items[:3])
        if proc_cpu:
            support = support + (proc_cpu[0].id,)
        if cpu_delta is not None:
            support = support + (cpu_delta.id,)
        hypotheses.append(
            CoreHypothesis(
                id="hyp_twin_agree",
                title="Simulation agreement with observed load",
                description=(
                    "Digital twin summaries align with graph/history load signals."
                ),
                supporting_evidence=support,
                confidence=78.0,
            )
        )

    if patterns and mem_items:
        support = tuple(e.id for e in mem_items[:3])
        hypotheses.append(
            CoreHypothesis(
                id="hyp_memory_pattern",
                title="Operational memory pattern match",
                description=patterns[0],
                supporting_evidence=support,
                confidence=70.0,
            )
        )

    return tuple(hypotheses)
