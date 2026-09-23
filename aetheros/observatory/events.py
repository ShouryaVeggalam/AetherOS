"""Event detection and observation derivation for the observatory.

Analysis only — no rendering, no OS mutation.
"""

from __future__ import annotations

from datetime import datetime, timezone

from aetheros.observatory.models import SystemEvent, TelemetryPoint

CPU_SPIKE_DELTA = 20.0
CPU_SPIKE_WINDOW_SECONDS = 5.0
MEMORY_PRESSURE_THRESHOLD = 85.0


def detect_events(
    history: tuple[TelemetryPoint, ...],
    current: TelemetryPoint,
    previous: TelemetryPoint | None,
) -> list[SystemEvent]:
    """Detect new system events from recent telemetry history.

    Args:
        history: Recent points oldest → newest (including current).
        current: Newest point.
        previous: Prior point, if any.

    Returns:
        Newly detected SystemEvent values.
    """

    found: list[SystemEvent] = []
    intent_event = _intent_changed(previous, current)
    if intent_event is not None:
        found.append(intent_event)
    spike = _cpu_spike(history, current)
    if spike is not None:
        found.append(spike)
    pressure = _memory_pressure(previous, current)
    if pressure is not None:
        found.append(pressure)
    return found


def research_completed_event(*, winner: str, score: float) -> SystemEvent:
    """Build a research-completed event from pipeline results."""

    return SystemEvent(
        timestamp=datetime.now(timezone.utc),
        type="research_completed",
        severity="info",
        title="Research Completed",
        description=f"Winner: {winner} (score {score:.0f})",
    )


def safety_blocked_event(*, title: str, reason: str) -> SystemEvent:
    """Build a safety-blocked event when a recommendation is rejected."""

    return SystemEvent(
        timestamp=datetime.now(timezone.utc),
        type="safety_blocked",
        severity="warning",
        title="Safety Blocked",
        description=f"{title}: {reason}",
    )


def derive_observations(
    history: tuple[TelemetryPoint, ...],
    events: tuple[SystemEvent, ...],
) -> tuple[str, ...]:
    """Derive factual observations from history (never invent claims).

    Args:
        history: Recent telemetry points.
        events: Recent system events.

    Returns:
        Short observation strings grounded in measured data.
    """

    notes: list[str] = []
    if len(history) >= 2:
        notes.extend(_cpu_change_observation(history))
        notes.extend(_intent_stability_observation(history))
        notes.extend(_memory_recovery_observation(history))
    for event in events[-3:]:
        if event.type == "research_completed":
            notes.append(f"Research finished — {event.description}")
        if event.type == "safety_blocked":
            notes.append(f"Safety blocked a recommendation — {event.description}")
    return tuple(notes[:5])


def _intent_changed(
    previous: TelemetryPoint | None,
    current: TelemetryPoint,
) -> SystemEvent | None:
    """Emit intent_changed when the profile name differs."""

    if previous is None or previous.intent == current.intent:
        return None
    return SystemEvent(
        timestamp=current.timestamp,
        type="intent_changed",
        severity="info",
        title="Intent Changed",
        description=f"{previous.intent} → {current.intent}",
    )


def _cpu_spike(
    history: tuple[TelemetryPoint, ...],
    current: TelemetryPoint,
) -> SystemEvent | None:
    """CPU spike when usage rises >20% within about 5 seconds."""

    baseline = _point_near(history, current, CPU_SPIKE_WINDOW_SECONDS)
    if baseline is None:
        return None
    delta = current.cpu - baseline.cpu
    if delta <= CPU_SPIKE_DELTA:
        return None
    return SystemEvent(
        timestamp=current.timestamp,
        type="cpu_spike",
        severity="critical" if current.cpu >= 95 else "warning",
        title="CPU Spike",
        description=f"CPU rose {delta:.0f}% in ~5s (now {current.cpu:.0f}%).",
    )


def _memory_pressure(
    previous: TelemetryPoint | None,
    current: TelemetryPoint,
) -> SystemEvent | None:
    """Memory pressure when usage crosses above 85%."""

    if current.memory < MEMORY_PRESSURE_THRESHOLD:
        return None
    if previous is not None and previous.memory >= MEMORY_PRESSURE_THRESHOLD:
        return None
    return SystemEvent(
        timestamp=current.timestamp,
        type="memory_pressure",
        severity="warning",
        title="Memory Pressure",
        description=f"Memory exceeded 85% (now {current.memory:.0f}%).",
    )


def _point_near(
    history: tuple[TelemetryPoint, ...],
    current: TelemetryPoint,
    seconds: float,
) -> TelemetryPoint | None:
    """Find the newest point at least `seconds` older than current."""

    target = current.timestamp.timestamp() - seconds
    candidate: TelemetryPoint | None = None
    for point in history:
        if point.timestamp.timestamp() <= target:
            candidate = point
    return candidate


def _cpu_change_observation(history: tuple[TelemetryPoint, ...]) -> list[str]:
    """Observe measured CPU delta over the available window."""

    first, last = history[0], history[-1]
    delta = last.cpu - first.cpu
    span = max(1, int(last.timestamp.timestamp() - first.timestamp.timestamp()))
    if abs(delta) < 10:
        return []
    direction = "increased" if delta > 0 else "decreased"
    return [f"CPU {direction} by {abs(delta):.0f}% over {span}s."]


def _intent_stability_observation(history: tuple[TelemetryPoint, ...]) -> list[str]:
    """Observe how long the current intent has been unchanged."""

    current = history[-1].intent
    started = history[-1].timestamp
    for point in reversed(history):
        if point.intent != current:
            break
        started = point.timestamp
    seconds = int(history[-1].timestamp.timestamp() - started.timestamp())
    if seconds < 60:
        return []
    minutes = seconds // 60
    return [f"{current} intent has remained stable for {minutes} minute(s)."]


def _memory_recovery_observation(history: tuple[TelemetryPoint, ...]) -> list[str]:
    """Observe memory recovering from above-threshold pressure."""

    if len(history) < 2:
        return []
    last = history[-1]
    if last.memory >= MEMORY_PRESSURE_THRESHOLD:
        return []
    saw_pressure = any(p.memory >= MEMORY_PRESSURE_THRESHOLD for p in history[:-1])
    if not saw_pressure:
        return []
    return ["Memory pressure recovered automatically."]
