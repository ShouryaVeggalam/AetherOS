"""Intent resolver — evidence-backed intent from process + profile + history.

Never invents an intent without measurable evidence. Manual profile alone is
accepted as evidence with reduced confidence when no process/history cues exist.
"""

from __future__ import annotations

from aetheros.context.models import IntentContext, IntentName, IntentSource
from aetheros.intent.profiles import (
    AI_TRAINING,
    BALANCED,
    BATTERY_SAVER,
    CODING,
    GAMING,
    VIDEO_EDITING,
)
from aetheros.observatory.models import TelemetryPoint

# Map dashboard / IntentEngine profile names → canonical P8 keys.
PROFILE_TO_INTENT: dict[str, IntentName] = {
    CODING: "CODING",
    AI_TRAINING: "AI",
    GAMING: "GAMING",
    VIDEO_EDITING: "EDITING",
    BATTERY_SAVER: "BATTERY",
    BALANCED: "BALANCED",
    "Coding": "CODING",
    "AI Training": "AI",
    "Gaming": "GAMING",
    "Video Editing": "EDITING",
    "Battery Saver": "BATTERY",
    "Balanced": "BALANCED",
}

# Foreground process substrings → intent (lowercase match).
PROCESS_CUES: tuple[tuple[str, IntentName], ...] = (
    ("cursor", "CODING"),
    ("code", "CODING"),
    ("vim", "CODING"),
    ("nvim", "CODING"),
    ("pycharm", "CODING"),
    ("python", "CODING"),
    ("node", "CODING"),
    ("steam", "GAMING"),
    ("game", "GAMING"),
    ("minecraft", "GAMING"),
    ("premiere", "EDITING"),
    ("final cut", "EDITING"),
    ("davinci", "EDITING"),
    ("blender", "EDITING"),
    ("photoshop", "EDITING"),
    ("jupyter", "AI"),
    ("pytorch", "AI"),
    ("ollama", "AI"),
    ("llama", "AI"),
    ("tensor", "AI"),
)


def resolve_intent(
    *,
    manual_profile: str | None,
    foreground_process: str | None,
    history: tuple[TelemetryPoint, ...] = (),
    battery_percent: float | None = None,
    intent_duration_seconds: float = 0.0,
) -> IntentContext:
    """Resolve IntentContext from available evidence only.

    Args:
        manual_profile: Active IntentEngine profile name, if any.
        foreground_process: Dominant process name from telemetry/graph.
        history: Observatory points (read-only).
        battery_percent: Optional battery reading for BATTERY bias.
        intent_duration_seconds: How long the manual intent has been active.
    """

    votes: list[tuple[IntentName, int, IntentSource]] = []

    manual_key = _from_profile(manual_profile)
    if manual_key is not None:
        votes.append((manual_key, 55, "manual"))

    process_key = _from_process(foreground_process)
    if process_key is not None:
        votes.append((process_key, 70, "foreground"))

    history_key = _from_history(history)
    if history_key is not None:
        votes.append((history_key, 60, "history"))

    if battery_percent is not None and battery_percent <= 20.0:
        votes.append(("BATTERY", 65, "foreground"))

    if not votes:
        # Absolute fallback — explicit lack of evidence, low confidence.
        return IntentContext(
            name="BALANCED",
            confidence=15,
            source="manual",
            duration=max(0.0, intent_duration_seconds),
        )

    tallies: dict[IntentName, list[tuple[int, IntentSource]]] = {}
    for name, score, source in votes:
        tallies.setdefault(name, []).append((score, source))

    best_name = max(
        tallies,
        key=lambda key: sum(score for score, _ in tallies[key]),
    )
    entries = tallies[best_name]
    confidence = min(100, int(sum(score for score, _ in entries) / len(entries)))
    sources = {source for _, source in entries}
    if len(sources) > 1:
        source: IntentSource = "combined"
        confidence = min(100, confidence + 10)
    else:
        source = next(iter(sources))
    return IntentContext(
        name=best_name,
        confidence=confidence,
        source=source,
        duration=max(0.0, intent_duration_seconds),
    )


def _from_profile(profile: str | None) -> IntentName | None:
    if not profile:
        return None
    return PROFILE_TO_INTENT.get(profile.strip())


def _from_process(name: str | None) -> IntentName | None:
    if not name:
        return None
    lowered = name.lower()
    for needle, intent in PROCESS_CUES:
        if needle in lowered:
            return intent
    return None


def _from_history(history: tuple[TelemetryPoint, ...]) -> IntentName | None:
    """Majority intent label among recent history points with known profiles."""

    if len(history) < 3:
        return None
    window = history[-min(len(history), 30) :]
    counts: dict[IntentName, int] = {}
    for point in window:
        key = _from_profile(point.intent)
        if key is None:
            continue
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return None
    winner = max(counts, key=counts.get)
    if counts[winner] < 3:
        return None
    return winner
