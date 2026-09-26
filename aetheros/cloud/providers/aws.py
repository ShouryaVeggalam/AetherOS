"""AWS provider adapter — read-only EC2 / EBS / VPC / RDS observation.

Never calls boto3 mutate APIs. Never provisions, terminates, or modifies
resources. Inventory is supplied as plain mappings (fixtures or external
export); credentials are never accepted.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aetheros.cloud.models import (
    PROVIDER_AWS,
    CloudProvider,
    CloudResource,
)

_SUPPORTED = frozenset({"ec2", "ebs", "vpc", "rds"})


def _demo_inventory() -> list[dict[str, Any]]:
    """Static demo inventory for dashboard seeding (read-only)."""

    return [
        {
            "id": "i-0a1b2c3d",
            "type": "ec2",
            "name": "web-1",
            "region": "us-east-1",
            "metadata": {"instance_type": "t3.medium", "state": "running"},
        },
        {
            "id": "vol-09f8e7d6",
            "type": "ebs",
            "name": "web-1-root",
            "region": "us-east-1",
            "metadata": {"size_gb": 30, "encrypted": True},
        },
        {
            "id": "vpc-01234567",
            "type": "vpc",
            "name": "prod-vpc",
            "region": "us-east-1",
            "metadata": {"cidr": "10.0.0.0/16"},
        },
        {
            "id": "db-aurora-1",
            "type": "rds",
            "name": "orders-db",
            "region": "us-east-1",
            "metadata": {"engine": "aurora-postgresql", "multi_az": True},
        },
    ]


class AWSProvider:
    """Observe AWS inventory as normalized CloudResource rows."""

    kind: str = PROVIDER_AWS

    def __init__(self, provider: CloudProvider | None = None) -> None:
        self.provider = provider or CloudProvider(
            id="aws-us-east-1",
            name="AWS",
            version="2016-11-15",
            region="us-east-1",
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
                    provider=PROVIDER_AWS,
                    type=rtype,
                    name=str(row.get("name") or row.get("id") or "").strip(),
                    region=str(row.get("region") or self.provider.region).strip(),
                    metadata=dict(row.get("metadata") or {}),
                )
            )
        return tuple(out)
