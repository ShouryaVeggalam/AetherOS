"""Robotics fleet registry — aggregate read-only fleet view."""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.robotics.autonomy import AutonomyProfile, seed_autonomy
from aetheros.robotics.telemetry import RobotTelemetry, seed_robot_telemetry


@dataclass(frozen=True, slots=True)
class FleetSnapshot:
    """Immutable robotics fleet summary."""

    robots: tuple[RobotTelemetry, ...]
    autonomy: tuple[AutonomyProfile, ...]
    online_count: int
    mean_battery: float


@dataclass
class RobotFleet:
    """Read-only fleet facade for Horizon."""

    def snapshot(self) -> FleetSnapshot:
        """Build a fleet snapshot from seeded catalogs."""

        robots = seed_robot_telemetry()
        autonomy = seed_autonomy()
        mean_batt = sum(r.battery_percent for r in robots) / len(robots)
        return FleetSnapshot(
            robots=robots,
            autonomy=autonomy,
            online_count=len(robots),
            mean_battery=round(mean_batt, 1),
        )
