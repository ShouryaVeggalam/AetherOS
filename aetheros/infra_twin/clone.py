"""Clone infrastructure twin snapshots — deep immutable copies.

Never mutates the source snapshot. Clones receive a new id and optional
timestamp bump for simulation lineage.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from aetheros.infra_twin.models import InfrastructureSnapshot, TopologyNode


def clone_snapshot(
    snapshot: InfrastructureSnapshot,
    *,
    new_id: str | None = None,
    timestamp: datetime | None = None,
) -> InfrastructureSnapshot:
    """Return a deep immutable copy of ``snapshot`` (simulation workspace)."""

    moment = timestamp or snapshot.timestamp
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    nodes = tuple(
        TopologyNode(
            id=node.id,
            kind=node.kind,
            region=node.region,
            provider=node.provider,
            capacity=node.capacity,
            load=node.load,
            latency_ms=node.latency_ms,
            available=node.available,
            metadata=dict(node.metadata),
        )
        for node in snapshot.topology
    )
    return InfrastructureSnapshot(
        id=new_id or f"clone-{uuid.uuid4().hex[:12]}",
        timestamp=moment,
        topology=nodes,
        resources=tuple(snapshot.resources),
        regions=tuple(snapshot.regions),
    )
