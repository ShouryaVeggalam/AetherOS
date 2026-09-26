"""Docker provider adapter — read-only Container / Image observation.

Never executes docker mutate commands (run/rm/build/push). Never talks to
a Docker daemon with write intent. Credentials are never accepted.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aetheros.cloud.models import (
    PROVIDER_DOCKER,
    CloudProvider,
    CloudResource,
)

_SUPPORTED = frozenset({"container", "image"})


def _demo_inventory() -> list[dict[str, Any]]:
    """Static demo inventory for dashboard seeding (read-only)."""

    return [
        {
            "id": "ctr-aether-api",
            "type": "container",
            "name": "aether-api",
            "region": "local",
            "metadata": {"image": "aetheros/api:5.0.0", "state": "running"},
        },
        {
            "id": "img-aetheros-api",
            "type": "image",
            "name": "aetheros/api:5.0.0",
            "region": "local",
            "metadata": {"size_mb": 180},
        },
    ]


class DockerProvider:
    """Observe Docker inventory as normalized CloudResource rows."""

    kind: str = PROVIDER_DOCKER

    def __init__(self, provider: CloudProvider | None = None) -> None:
        self.provider = provider or CloudProvider(
            id="docker-local",
            name="Docker",
            version="24.0",
            region="local",
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
                    provider=PROVIDER_DOCKER,
                    type=rtype,
                    name=str(row.get("name") or row.get("id") or "").strip(),
                    region=str(row.get("region") or self.provider.region).strip(),
                    metadata=dict(row.get("metadata") or {}),
                )
            )
        return tuple(out)
