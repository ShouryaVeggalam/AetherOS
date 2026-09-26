"""GCP provider adapter — read-only Compute / Disk / Network observation.

Never calls GCP mutate APIs. Never provisions or deletes resources.
Credentials are never accepted.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aetheros.cloud.models import (
    PROVIDER_GCP,
    CloudProvider,
    CloudResource,
)

_SUPPORTED = frozenset({"compute", "disk", "network"})


def _demo_inventory() -> list[dict[str, Any]]:
    """Static demo inventory for dashboard seeding (read-only)."""

    return [
        {
            "id": "gce-worker-1",
            "type": "compute",
            "name": "worker-1",
            "region": "us-central1",
            "metadata": {"machine": "e2-standard-2", "zone": "us-central1-a"},
        },
        {
            "id": "pd-worker-1",
            "type": "disk",
            "name": "worker-1-boot",
            "region": "us-central1",
            "metadata": {"size_gb": 50, "type": "pd-balanced"},
        },
        {
            "id": "vpc-default",
            "type": "network",
            "name": "default",
            "region": "global",
            "metadata": {"auto_create_subnetworks": True},
        },
    ]


class GCPProvider:
    """Observe GCP inventory as normalized CloudResource rows."""

    kind: str = PROVIDER_GCP

    def __init__(self, provider: CloudProvider | None = None) -> None:
        self.provider = provider or CloudProvider(
            id="gcp-us-central1",
            name="Google Cloud",
            version="v1",
            region="us-central1",
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
                    provider=PROVIDER_GCP,
                    type=rtype,
                    name=str(row.get("name") or row.get("id") or "").strip(),
                    region=str(row.get("region") or self.provider.region).strip(),
                    metadata=dict(row.get("metadata") or {}),
                )
            )
        return tuple(out)
