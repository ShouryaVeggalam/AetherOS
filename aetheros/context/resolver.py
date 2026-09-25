"""Context resolver — thin orchestration helpers for intent + history.

Keeps builder focused on aggregation; resolver exposes named entry points
used by ContextEngine and optional adapters.
"""

from __future__ import annotations

from aetheros.context.history import match_historical_pattern
from aetheros.context.intent import resolve_intent
from aetheros.context.models import HistoricalPattern, IntentContext, IntentName
from aetheros.observatory.models import TelemetryPoint


def resolve_operational_intent(
    *,
    manual_profile: str | None,
    foreground_process: str | None,
    history: tuple[TelemetryPoint, ...] = (),
    battery_percent: float | None = None,
    intent_duration_seconds: float = 0.0,
) -> IntentContext:
    """Public intent resolution entry (delegates to intent.resolve_intent)."""

    return resolve_intent(
        manual_profile=manual_profile,
        foreground_process=foreground_process,
        history=history,
        battery_percent=battery_percent,
        intent_duration_seconds=intent_duration_seconds,
    )


def resolve_historical_match(
    *,
    cpu: float,
    memory: float,
    disk: float,
    intent: IntentName | None,
    history: tuple[TelemetryPoint, ...],
) -> HistoricalPattern | None:
    """Public historical matcher entry."""

    return match_historical_pattern(
        cpu=cpu,
        memory=memory,
        disk=disk,
        intent=intent,
        history=history,
    )
