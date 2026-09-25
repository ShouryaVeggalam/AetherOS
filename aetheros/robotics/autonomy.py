"""Autonomy descriptors — declared modes only.

Never switches autonomy levels on hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AutonomyLevel = Literal["manual", "supervised", "autonomous"]


@dataclass(frozen=True, slots=True)
class AutonomyProfile:
    """Declared autonomy posture for a robot (inventory only)."""

    robot_id: str
    level: AutonomyLevel
    requires_human_approval: bool
    notes: str


def seed_autonomy() -> tuple[AutonomyProfile, ...]:
    """Synthetic autonomy catalog — humans always approve actuation."""

    return (
        AutonomyProfile(
            "robot.de.1",
            "supervised",
            True,
            "Supervised patrol — human approval required for mode changes.",
        ),
        AutonomyProfile(
            "robot.us.1",
            "supervised",
            True,
            "Inspection route — no unsupervised tool use.",
        ),
        AutonomyProfile(
            "robot.jp.1",
            "manual",
            True,
            "Idle / docked — manual only.",
        ),
    )
