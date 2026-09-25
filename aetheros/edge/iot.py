"""IoT device registry — catalog of constrained devices.

Never flips relays or writes firmware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

IoTProtocol = Literal["mqtt", "coap", "lora", "ble"]


@dataclass(frozen=True, slots=True)
class IoTDevice:
    """One immutable IoT endpoint descriptor."""

    device_id: str
    name: str
    protocol: IoTProtocol
    region_id: str
    gateway_id: str
    online: bool


def seed_iot() -> tuple[IoTDevice, ...]:
    """Synthetic IoT catalog for Horizon overlays."""

    return (
        IoTDevice(
            "iot.eu.meter.1",
            "EU-Power-Meter",
            "mqtt",
            "region.eu",
            "edge.gw.de",
            True,
        ),
        IoTDevice(
            "iot.na.cam.1",
            "NA-Dock-Cam",
            "coap",
            "region.na",
            "edge.gw.us",
            True,
        ),
        IoTDevice(
            "iot.apac.soil.1",
            "APAC-Soil-Probe",
            "lora",
            "region.apac",
            "edge.gw.sg",
            False,
        ),
    )
