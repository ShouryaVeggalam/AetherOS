"""Robotics telemetry — read-only fleet observations.

Never sends motor commands. Never modifies autonomy modes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class RobotTelemetry:
    """One immutable robot status sample."""

    robot_id: str
    region_id: str
    battery_percent: float
    pose_x: float
    pose_y: float
    task: str
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate battery."""

        if not 0.0 <= self.battery_percent <= 100.0:
            raise ValueError("battery_percent must be in [0, 100]")


def seed_robot_telemetry() -> tuple[RobotTelemetry, ...]:
    """Synthetic robot telemetry for Horizon overlays."""

    now = datetime.now(UTC)
    return (
        RobotTelemetry("robot.de.1", "region.eu", 81.0, 12.4, 3.1, "patrol", now),
        RobotTelemetry("robot.us.1", "region.na", 64.0, -2.0, 8.5, "inspect", now),
        RobotTelemetry("robot.jp.1", "region.apac", 92.0, 0.5, 0.2, "idle", now),
    )
