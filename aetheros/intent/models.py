"""Intent-engine data contracts.

An IntentProfile describes how the user wants AetherOS to prioritize
advice. Profiles never execute commands — they only change scoring.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IntentProfile:
    """One user intent with resource priority weights.

    Attributes:
        name: Canonical profile name (e.g. "Coding").
        description: Short focus statement for the UI.
        cpu_weight: Emphasis on CPU-related pressure.
        memory_weight: Emphasis on memory pressure.
        disk_weight: Emphasis on disk pressure.
        latency_weight: Emphasis on interactive / low-latency concerns
            (also used as a GPU placeholder where noted).
        efficiency_weight: Emphasis on power efficiency / background quiet.
    """

    name: str
    description: str
    cpu_weight: int
    memory_weight: int
    disk_weight: int
    latency_weight: int
    efficiency_weight: int

    def __post_init__(self) -> None:
        """Reject negative weights."""

        for field_name in (
            "cpu_weight",
            "memory_weight",
            "disk_weight",
            "latency_weight",
            "efficiency_weight",
        ):
            if getattr(self, field_name) < 0:
                raise ValueError(f"{field_name} must be >= 0")
