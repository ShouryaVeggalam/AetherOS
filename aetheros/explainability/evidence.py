"""Evidence collector — gather traceable facts for explanations.

Never fabricates values. Missing inputs yield fewer Evidence items.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from statistics import mean

from aetheros.explainability.models import Evidence
from aetheros.intent.models import IntentProfile
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.simulation.models import SimulationResult
from aetheros.telemetry.models import ProcessSnapshot


@dataclass(frozen=True, slots=True)
class EvidenceBundle:
    """Collected evidence plus quality signals for confidence scoring.

    Attributes:
        items: Immutable evidence facts.
        sample_count: Number of history points available.
        has_simulation: Whether a SimulationResult was supplied.
        intent_certainty: 0–100 certainty from profile weight contrast.
    """

    items: tuple[Evidence, ...]
    sample_count: int
    has_simulation: bool
    intent_certainty: int


def collect_evidence(
    snapshot: TelemetrySnapshot,
    *,
    history: tuple[TelemetryPoint, ...] = (),
    intent: IntentProfile | None = None,
    simulation: SimulationResult | None = None,
    processes: tuple[ProcessSnapshot, ...] = (),
) -> EvidenceBundle:
    """Collect evidence from real inputs only.

    Args:
        snapshot: Current flat telemetry.
        history: Observatory telemetry points (oldest → newest).
        intent: Active intent profile, if known.
        simulation: Optional simulation for the recommendation.
        processes: Optional process samples with CPU percents.

    Returns:
        An EvidenceBundle. Never invents metrics.
    """

    stamp = snapshot.timestamp
    items: list[Evidence] = []
    items.extend(_telemetry_evidence(snapshot, stamp))
    items.extend(_process_evidence(processes, stamp))
    items.extend(_history_evidence(history, stamp))
    if intent is not None:
        items.extend(_intent_evidence(intent, stamp))
    if simulation is not None:
        items.extend(_simulation_evidence(simulation, stamp))
    return EvidenceBundle(
        items=tuple(items),
        sample_count=len(history),
        has_simulation=simulation is not None,
        intent_certainty=_intent_certainty(intent),
    )


def _telemetry_evidence(
    snapshot: TelemetrySnapshot,
    stamp: datetime,
) -> list[Evidence]:
    """Evidence from the live telemetry snapshot."""

    rows = [
        ("cpu", snapshot.cpu_percent, f"CPU at {snapshot.cpu_percent:.0f}%."),
        (
            "memory",
            snapshot.memory_percent,
            f"Memory at {snapshot.memory_percent:.0f}%.",
        ),
        ("disk", snapshot.disk_percent, f"Disk at {snapshot.disk_percent:.0f}%."),
    ]
    out = [
        Evidence("telemetry", metric, value, stamp, text)
        for metric, value, text in rows
    ]
    if snapshot.battery_percent is not None:
        batt = snapshot.battery_percent
        out.append(
            Evidence(
                "telemetry",
                "battery",
                batt,
                stamp,
                f"Battery at {batt:.0f}%.",
            )
        )
    return out


def _process_evidence(
    processes: tuple[ProcessSnapshot, ...],
    stamp: datetime,
) -> list[Evidence]:
    """Evidence from top process CPU when samples are available."""

    if not processes:
        return []
    top = max(processes, key=lambda p: p.cpu_percent)
    if top.cpu_percent <= 0.0:
        return []
    return [
        Evidence(
            "telemetry",
            "process_cpu",
            top.cpu_percent,
            stamp,
            f"{top.name} consumed {top.cpu_percent:.0f}% CPU.",
        )
    ]


def _history_evidence(
    history: tuple[TelemetryPoint, ...],
    stamp: datetime,
) -> list[Evidence]:
    """Evidence from last-5-minute / last-hour windows when present."""

    if not history:
        return []
    out: list[Evidence] = []
    five = _window(history, seconds=300)
    hour = _window(history, seconds=3600)
    if five:
        out.append(_avg_evidence(five, "cpu", "5 minutes", stamp))
        out.extend(_pressure_streak(five, stamp))
    if hour and len(hour) >= len(five) + 1:
        out.append(_avg_evidence(hour, "cpu", "available hour window", stamp))
    if len(history) >= 10:
        out.append(_daily_style_average(history, stamp))
    return out


def _avg_evidence(
    points: tuple[TelemetryPoint, ...],
    metric: str,
    label: str,
    stamp: datetime,
) -> Evidence:
    """Average one metric over a real history window."""

    values = [getattr(p, metric) for p in points]
    avg = mean(values)
    return Evidence(
        "history",
        f"{metric}_avg",
        avg,
        stamp,
        (
            f"CPU averaged {avg:.0f}% over {label}."
            if metric == "cpu"
            else f"{metric.capitalize()} averaged {avg:.0f}% over {label}."
        ),
    )


def _pressure_streak(
    points: tuple[TelemetryPoint, ...],
    stamp: datetime,
) -> list[Evidence]:
    """Count consecutive high-CPU samples at the end of the window."""

    if len(points) < 2:
        return []
    threshold = 85.0
    streak = 0
    for point in reversed(points):
        if point.cpu < threshold:
            break
        streak += 1
    if streak < 2:
        return []
    first = points[-streak]
    last = points[-1]
    seconds = max(
        1, int((_aware(last.timestamp) - _aware(first.timestamp)).total_seconds())
    )
    return [
        Evidence(
            "history",
            "cpu_streak",
            float(seconds),
            stamp,
            f"CPU remained above {threshold:.0f}% for {seconds} seconds.",
        )
    ]


def _daily_style_average(
    history: tuple[TelemetryPoint, ...],
    stamp: datetime,
) -> Evidence:
    """Average over all available history (proxy when full day is absent)."""

    avg = mean(p.cpu for p in history)
    minutes = max(
        1,
        int(
            (
                _aware(history[-1].timestamp) - _aware(history[0].timestamp)
            ).total_seconds()
            / 60
        ),
    )
    return Evidence(
        "history",
        "cpu_session_avg",
        avg,
        stamp,
        f"Session CPU average {avg:.0f}% across {minutes} minutes of history.",
    )


def _intent_evidence(intent: IntentProfile, stamp: datetime) -> list[Evidence]:
    """Evidence from the active intent profile weights."""

    lines: list[Evidence] = [
        Evidence(
            "intent",
            "profile",
            float(intent.latency_weight),
            stamp,
            f"{intent.name} profile active — {intent.description}",
        )
    ]
    if intent.latency_weight >= intent.efficiency_weight:
        lines.append(
            Evidence(
                "intent",
                "latency",
                float(intent.latency_weight),
                stamp,
                f"{intent.name} prioritizes latency over efficiency.",
            )
        )
    else:
        lines.append(
            Evidence(
                "intent",
                "efficiency",
                float(intent.efficiency_weight),
                stamp,
                f"{intent.name} prioritizes efficiency over latency.",
            )
        )
    return lines


def _simulation_evidence(
    simulation: SimulationResult,
    stamp: datetime,
) -> list[Evidence]:
    """Evidence from a real SimulationResult only."""

    cpu_delta = simulation.projected_cpu_percent
    improvement = simulation.overall_improvement
    return [
        Evidence(
            "simulation",
            "projected_cpu",
            cpu_delta,
            stamp,
            f"{simulation.strategy_title} reduced predicted CPU to "
            f"{cpu_delta:.0f}%.",
        ),
        Evidence(
            "simulation",
            "stability",
            simulation.stability_score,
            stamp,
            f"Simulation stability score {simulation.stability_score:.0f}.",
        ),
        Evidence(
            "simulation",
            "improvement",
            improvement,
            stamp,
            f"Simulation predicts {improvement:.0f}% overall improvement.",
        ),
    ]


def _intent_certainty(intent: IntentProfile | None) -> int:
    """Derive 0–100 certainty from weight contrast (not hardcoded labels)."""

    if intent is None:
        return 0
    weights = (
        intent.cpu_weight,
        intent.memory_weight,
        intent.disk_weight,
        intent.latency_weight,
        intent.efficiency_weight,
    )
    total = sum(weights)
    if total <= 0:
        return 0
    peak = max(weights)
    contrast = (peak / total) * 100.0
    spread = (max(weights) - min(weights)) / max(1, max(weights))
    return int(max(0, min(100, contrast * 0.6 + spread * 100.0 * 0.4)))


def _window(
    history: tuple[TelemetryPoint, ...],
    *,
    seconds: int,
) -> tuple[TelemetryPoint, ...]:
    """Filter history to the last N seconds relative to the newest point."""

    if not history:
        return ()
    newest = _aware(history[-1].timestamp)
    cutoff = newest - timedelta(seconds=seconds)
    return tuple(p for p in history if _aware(p.timestamp) >= cutoff)


def _aware(value: datetime) -> datetime:
    """Ensure timezone-aware UTC for comparisons."""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
