"""Mobile device edge models — inventory only.

Never controls phones or tablets. Never pushes MDM commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MobileClass = Literal["phone", "tablet", "laptop"]


@dataclass(frozen=True, slots=True)
class MobileDevice:
    """One immutable mobile edge inventory record."""

    device_id: str
    name: str
    device_class: MobileClass
    region_id: str
    battery_percent: float | None
    online: bool

    def __post_init__(self) -> None:
        """Validate battery if present."""

        if (
            self.battery_percent is not None
            and not 0.0 <= self.battery_percent <= 100.0
        ):
            raise ValueError("battery_percent must be in [0, 100]")


def seed_mobiles() -> tuple[MobileDevice, ...]:
    """Synthetic mobile inventory for Horizon overlays."""

    return (
        MobileDevice(
            "mobile.na.1", "Field-Laptop-1", "laptop", "region.na", 72.0, True
        ),
        MobileDevice("mobile.eu.1", "Ops-Phone-1", "phone", "region.eu", 54.0, True),
        MobileDevice(
            "mobile.apac.1", "Survey-Tablet-1", "tablet", "region.apac", None, False
        ),
    )
