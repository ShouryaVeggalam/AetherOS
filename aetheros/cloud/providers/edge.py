"""Edge provider adapter — read-only Device / Gateway observation.

Never provisions edge fleets, never flashes firmware, never opens remote
shells. Credentials are never accepted.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aetheros.cloud.models import (
    PROVIDER_EDGE,
    CloudProvider,
    CloudResource,
)

_SUPPORTED = frozenset({"device", "gateway"})


def _demo_inventory() -> list[dict[str, Any]]:
    """Static demo inventory for dashboard seeding (read-only)."""

    return [
        {
            "id": "gw-hyd-01",
            "type": "gateway",
            "name": "hyd-gateway",
            "region": "ap-south-1",
            "metadata": {"firmware": "1.4.2", "online": True},
        },
        {
            "id": "dev-sensor-42",
            "type": "device",
            "name": "temp-sensor-42",
            "region": "ap-south-1",
            "metadata": {"kind": "temperature", "battery_pct": 88},
        },
    ]


class EdgeProvider:
    """Observe edge inventory as normalized CloudResource rows."""

    kind: str = PROVIDER_EDGE

    def __init__(self, provider: CloudProvider | None = None) -> None:
        self.provider = provider or CloudProvider(
            id="edge-ap-south-1",
            name="Edge",
            version="1.0",
            region="ap-south-1",
            connected=True,
        )

    def observe(
        self,
        inventory: Sequence[Mapping[str, Any]] | None = None,
    ) -> tuple[CloudResource, ...]:
        """Normalize inventory rows into CloudResource (read-only)."""

        rows = list(inventory) if inventory is not None else _demo_inventory()
        out: list[CloudResource] = []
        for row in rows:
            rtype = str(row.get("type") or "").strip().lower()
            if rtype not in _SUPPORTED:
                continue
            out.append(
                CloudResource(
                    id=str(row.get("id") or "").strip(),
                    provider=PROVIDER_EDGE,
                    type=rtype,
                    name=str(row.get("name") or row.get("id") or "").strip(),
                    region=str(row.get("region") or self.provider.region).strip(),
                    metadata=dict(row.get("metadata") or {}),
                )
            )
        return tuple(out)
