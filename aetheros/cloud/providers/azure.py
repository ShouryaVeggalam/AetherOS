"""Azure provider adapter — read-only VM / Storage / Network observation.

Never calls Azure mutate APIs. Never provisions or deletes resources.
Credentials are never accepted.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aetheros.cloud.models import (
    PROVIDER_AZURE,
    CloudProvider,
    CloudResource,
)

_SUPPORTED = frozenset({"vm", "storage", "network"})


def _demo_inventory() -> list[dict[str, Any]]:
    """Static demo inventory for dashboard seeding (read-only)."""

    return [
        {
            "id": "vm-app-01",
            "type": "vm",
            "name": "app-01",
            "region": "eastus",
            "metadata": {"sku": "Standard_D2s_v3", "power": "running"},
        },
        {
            "id": "st-prodlogs",
            "type": "storage",
            "name": "prodlogs",
            "region": "eastus",
            "metadata": {"kind": "StorageV2", "tier": "Hot"},
        },
        {
            "id": "vnet-prod",
            "type": "network",
            "name": "prod-vnet",
            "region": "eastus",
            "metadata": {"address_space": "10.1.0.0/16"},
        },
    ]


class AzureProvider:
    """Observe Azure inventory as normalized CloudResource rows."""

    kind: str = PROVIDER_AZURE

    def __init__(self, provider: CloudProvider | None = None) -> None:
        self.provider = provider or CloudProvider(
            id="azure-eastus",
            name="Azure",
            version="2024-03-01",
            region="eastus",
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
                    provider=PROVIDER_AZURE,
                    type=rtype,
                    name=str(row.get("name") or row.get("id") or "").strip(),
                    region=str(row.get("region") or self.provider.region).strip(),
                    metadata=dict(row.get("metadata") or {}),
                )
            )
        return tuple(out)
