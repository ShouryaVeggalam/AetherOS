"""Historical matcher — find similar telemetry situations (read-only).

Uses observatory ``TelemetryPoint`` history only. No schema changes, no writes.
"""

from __future__ import annotations

from aetheros.context.intent import PROFILE_TO_INTENT
from aetheros.context.models import HistoricalPattern, IntentName
from aetheros.observatory.models import TelemetryPoint


def match_historical_pattern(
    *,
    cpu: float,
    memory: float,
    disk: float,
    intent: IntentName | None,
    history: tuple[TelemetryPoint, ...],
    window: int = 60,
) -> HistoricalPattern | None:
    """Return the best similar historical pattern, or None if evidence is weak.

    Similarity is based on resource distance and optional intent agreement.
    Requires at least 3 comparable samples.
    """

    if len(history) < 3:
        return None
    samples = history[-min(len(history), max(window, 3)) :]
    scored: list[tuple[float, TelemetryPoint]] = []
    for point in samples:
        distance = (
            abs(point.cpu - cpu)
            + abs(point.memory - memory)
            + abs(point.disk - disk)
        ) / 3.0
        similarity = max(0.0, 100.0 - distance)
        if intent is not None:
            hist_intent = PROFILE_TO_INTENT.get(point.intent)
            if hist_intent == intent:
                similarity = min(100.0, similarity + 8.0)
            elif hist_intent is not None:
                similarity = max(0.0, similarity - 5.0)
        scored.append((similarity, point))

    scored.sort(key=lambda item: item[0], reverse=True)
    top = scored[: min(18, len(scored))]
    if not top:
        return None
    avg_similarity = sum(score for score, _ in top) / len(top)
    if avg_similarity < 40.0:
        return None
    label = _label_for(intent, top[0][1], avg_similarity)
    return HistoricalPattern(
        label=label,
        similarity=round(avg_similarity, 1),
        evidence_count=len(top),
    )


def _label_for(
    intent: IntentName | None,
    exemplar: TelemetryPoint,
    similarity: float,
) -> str:
    """Build an operator-facing pattern label from evidence."""

    hour = exemplar.timestamp.hour
    if 5 <= hour < 12:
        period = "Morning"
    elif 12 <= hour < 17:
        period = "Afternoon"
    elif 17 <= hour < 22:
        period = "Evening"
    else:
        period = "Late-night"
    intent_label = {
        "CODING": "Coding",
        "AI": "AI Training",
        "GAMING": "Gaming",
        "EDITING": "Editing",
        "BATTERY": "Battery Saver",
        "BALANCED": "Balanced",
    }.get(intent or "", exemplar.intent or "Workload")
    if similarity >= 85:
        quality = "Session"
    elif similarity >= 60:
        quality = "Pattern"
    else:
        quality = "Trace"
    return f"{period} {intent_label} {quality}"
