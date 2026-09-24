"""Observatory — temporal memory for AetherOS (v1.1)."""

from aetheros.observatory.events import (
    derive_observations,
    detect_events,
    research_completed_event,
    safety_blocked_event,
)
from aetheros.observatory.models import (
    GraphMetric,
    SystemEvent,
    TelemetryPoint,
    TimelineWindow,
)
from aetheros.observatory.recorder import HistoryRecorder
from aetheros.observatory.renderer import (
    ObservatoryPanel,
    render_ascii_graph,
    sparkline,
)
from aetheros.observatory.timeline import EventTimeline

# Backward-compatible aliases used by older dashboard imports/tests.
ObservatoryRecorder = HistoryRecorder
ObservatoryEvent = SystemEvent
ObservatoryPoint = TelemetryPoint


def detect_telemetry_events(previous, current, history=()):
    """Compatibility wrapper around detect_events."""

    hist = tuple(history) if history else ((previous,) if previous else ()) + (current,)
    return detect_events(hist, current, previous)


__all__ = [
    "EventTimeline",
    "GraphMetric",
    "HistoryRecorder",
    "ObservatoryEvent",
    "ObservatoryPanel",
    "ObservatoryPoint",
    "ObservatoryRecorder",
    "SystemEvent",
    "TelemetryPoint",
    "TimelineWindow",
    "derive_observations",
    "detect_events",
    "detect_telemetry_events",
    "render_ascii_graph",
    "research_completed_event",
    "safety_blocked_event",
    "sparkline",
]
