"""Edge sensor models — read-only IoT/sensor telemetry shapes.

Never actuates sensors. Never opens device buses.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

SensorKind = Literal["temperature", "humidity", "vibration", "power", "presence"]


@dataclass(frozen=True, slots=True)
class SensorReading:
    """One immutable sensor observation.

    Attributes:
        sensor_id: Stable sensor id.
        kind: Sensor modality.
        value: Numeric reading.
        unit: Unit label.
        timestamp: UTC sample time.
        region_id: Hosting region id.
    """

    sensor_id: str
    kind: SensorKind
    value: float
    unit: str
    timestamp: datetime
    region_id: str


def seed_sensors() -> tuple[SensorReading, ...]:
    """Return a small public catalog of synthetic sensor readings."""

    now = datetime.now(UTC)
    return (
        SensorReading("sensor.de.1", "temperature", 21.4, "C", now, "region.eu"),
        SensorReading("sensor.us.1", "power", 412.0, "W", now, "region.na"),
        SensorReading("sensor.sg.1", "humidity", 68.0, "%", now, "region.apac"),
    )
