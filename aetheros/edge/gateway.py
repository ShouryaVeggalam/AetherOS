"""Edge gateway — aggregates read-only edge inventories.

Gateways are logical aggregation points in the world graph.
They never open sockets to field devices from this process.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.edge.iot import IoTDevice, seed_iot
from aetheros.edge.mobile import MobileDevice, seed_mobiles
from aetheros.edge.sensor import SensorReading, seed_sensors


@dataclass(frozen=True, slots=True)
class EdgeInventory:
    """Immutable snapshot of edge-layer assets."""

    gateways: tuple[str, ...]
    sensors: tuple[SensorReading, ...]
    mobiles: tuple[MobileDevice, ...]
    iot: tuple[IoTDevice, ...]

    @property
    def online_ratio(self) -> float:
        """Fraction of mobile+iot devices marked online."""

        devices = (*self.mobiles, *self.iot)
        if not devices:
            return 0.0
        return sum(1 for d in devices if d.online) / len(devices)


@dataclass
class EdgeGateway:
    """Read-only edge aggregation facade."""

    def inventory(self) -> EdgeInventory:
        """Return the seeded edge inventory."""

        sensors = seed_sensors()
        mobiles = seed_mobiles()
        iot = seed_iot()
        gateways = tuple(sorted({d.gateway_id for d in iot}))
        return EdgeInventory(
            gateways=gateways,
            sensors=sensors,
            mobiles=mobiles,
            iot=iot,
        )
