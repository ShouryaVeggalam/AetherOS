"""Built-in intent profiles for AetherOS.

Six preset modes. Placeholder weights (GPU, brightness) live in
latency_weight or efficiency_weight and are documented in descriptions.
"""

from __future__ import annotations

from aetheros.intent.models import IntentProfile

# Canonical names used by IntentEngine.set_intent and the dashboard keys.
CODING = "Coding"
GAMING = "Gaming"
VIDEO_EDITING = "Video Editing"
BATTERY_SAVER = "Battery Saver"
AI_TRAINING = "AI Training"
BALANCED = "Balanced"

DEFAULT_INTENT = BALANCED

PROFILES: dict[str, IntentProfile] = {
    CODING: IntentProfile(
        name=CODING,
        description="Low latency development — stable CPU, fast editor response.",
        cpu_weight=10,
        memory_weight=15,
        disk_weight=5,
        latency_weight=25,  # CPU latency priority
        efficiency_weight=20,  # background penalty
    ),
    GAMING: IntentProfile(
        name=GAMING,
        description="Maximum foreground performance.",
        cpu_weight=35,  # foreground CPU
        memory_weight=10,
        disk_weight=5,
        latency_weight=20,  # GPU placeholder
        efficiency_weight=30,  # background penalty
    ),
    VIDEO_EDITING: IntentProfile(
        name=VIDEO_EDITING,
        description="High sustained throughput for media workloads.",
        cpu_weight=25,
        memory_weight=30,
        disk_weight=20,  # disk IO
        latency_weight=5,
        efficiency_weight=5,
    ),
    BATTERY_SAVER: IntentProfile(
        name=BATTERY_SAVER,
        description="Minimize power — prefer efficiency over peak speed.",
        cpu_weight=5,
        memory_weight=5,
        disk_weight=5,
        latency_weight=10,  # brightness placeholder
        efficiency_weight=30,  # CPU efficiency (+ background reduction via same knob)
    ),
    AI_TRAINING: IntentProfile(
        name=AI_TRAINING,
        description="Maximum compute for training and inference jobs.",
        cpu_weight=20,
        memory_weight=25,
        disk_weight=10,
        latency_weight=35,  # GPU placeholder
        efficiency_weight=0,
    ),
    BALANCED: IntentProfile(
        name=BALANCED,
        description="Equal emphasis across resources.",
        cpu_weight=20,
        memory_weight=20,
        disk_weight=20,
        latency_weight=20,
        efficiency_weight=20,
    ),
}

# Dashboard hotkeys 1–6 → profile name.
INTENT_HOTKEYS: dict[str, str] = {
    "1": CODING,
    "2": GAMING,
    "3": VIDEO_EDITING,
    "4": BATTERY_SAVER,
    "5": AI_TRAINING,
    "6": BALANCED,
}


def get_profile(name: str) -> IntentProfile:
    """Look up a profile by name (case-insensitive).

    Args:
        name: Profile name or common alias (e.g. "Editing").

    Returns:
        The matching IntentProfile.

    Raises:
        KeyError: When the name is unknown.
    """

    normalized = name.strip()
    aliases = {
        "editing": VIDEO_EDITING,
        "video": VIDEO_EDITING,
        "battery": BATTERY_SAVER,
        "ai": AI_TRAINING,
        "train": AI_TRAINING,
    }
    key = aliases.get(normalized.lower(), normalized)
    for profile_name, profile in PROFILES.items():
        if profile_name.lower() == key.lower():
            return profile
    raise KeyError(f"Unknown intent profile: {name!r}")


def list_profile_names() -> tuple[str, ...]:
    """Return all built-in profile names in display order."""

    return (
        CODING,
        GAMING,
        VIDEO_EDITING,
        BATTERY_SAVER,
        AI_TRAINING,
        BALANCED,
    )
