"""Kubernetes provider adapter — read-only Cluster / Node / Pod / Service.

Never executes kubectl. Never applies manifests. Never mutates cluster state.
Inventory is supplied as plain mappings; kubeconfig credentials are never
accepted or stored.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aetheros.cloud.models import (
    PROVIDER_KUBERNETES,
    CloudProvider,
    CloudResource,
)

_SUPPORTED = frozenset({"cluster", "node", "pod", "service"})


def _demo_inventory() -> list[dict[str, Any]]:
    """Static demo inventory for dashboard seeding (read-only)."""

    return [
        {
            "id": "eks-prod",
            "type": "cluster",
            "name": "prod",
            "region": "us-east-1",
            "metadata": {"version": "1.29", "nodes": 6},
        },
        {
            "id": "ip-10-0-1-12",
            "type": "node",
            "name": "node-a",
            "region": "us-east-1",
            "metadata": {"ready": True, "roles": "worker"},
        },
        {
            "id": "pod-api-7f8c9",
            "type": "pod",
            "name": "api-7f8c9",
            "region": "us-east-1",
            "metadata": {"namespace": "default", "phase": "Running"},
        },
        {
            "id": "svc-api",
            "type": "service",
            "name": "api",
            "region": "us-east-1",
            "metadata": {"namespace": "default", "type": "ClusterIP"},
        },
    ]


class KubernetesProvider:
    """Observe Kubernetes inventory as normalized CloudResource rows."""

    kind: str = PROVIDER_KUBERNETES

    def __init__(self, provider: CloudProvider | None = None) -> None:
        self.provider = provider or CloudProvider(
            id="k8s-prod",
            name="Kubernetes",
            version="1.29",
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
                    provider=PROVIDER_KUBERNETES,
                    type=rtype,
                    name=str(row.get("name") or row.get("id") or "").strip(),
                    region=str(row.get("region") or self.provider.region).strip(),
                    metadata=dict(row.get("metadata") or {}),
                )
            )
        return tuple(out)
