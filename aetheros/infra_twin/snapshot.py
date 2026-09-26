"""Infrastructure twin snapshot capture — immutable world-state builders.

Builds twin snapshots from cloud federation census or demo topology.
Never calls cloud mutation APIs.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from aetheros.cloud.models import CloudResource
from aetheros.cloud.models import InfrastructureSnapshot as CloudSnapshot
from aetheros.infra_twin.models import InfrastructureSnapshot, TopologyNode


def _new_id(prefix: str = "twin") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def demo_snapshot(*, timestamp: datetime | None = None) -> InfrastructureSnapshot:
    """Deterministic demo topology for dashboard / tests (simulation only)."""

    moment = timestamp or datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    nodes = (
        TopologyNode(
            id="node-aws-a",
            kind="node",
            region="us-east-1",
            provider="aws",
            capacity=100.0,
            load=42.0,
            latency_ms=4.0,
        ),
        TopologyNode(
            id="node-aws-b",
            kind="node",
            region="us-east-1",
            provider="aws",
            capacity=100.0,
            load=38.0,
            latency_ms=4.2,
        ),
        TopologyNode(
            id="node-aws-c",
            kind="node",
            region="us-west-2",
            provider="aws",
            capacity=100.0,
            load=55.0,
            latency_ms=12.0,
        ),
        TopologyNode(
            id="node-k8s-1",
            kind="node",
            region="us-east-1",
            provider="kubernetes",
            capacity=100.0,
            load=61.0,
            latency_ms=3.5,
            metadata={"role": "worker"},
        ),
        TopologyNode(
            id="node-k8s-2",
            kind="node",
            region="us-east-1",
            provider="kubernetes",
            capacity=100.0,
            load=47.0,
            latency_ms=3.8,
            metadata={"role": "worker"},
        ),
        TopologyNode(
            id="node-gcp-1",
            kind="compute",
            region="us-central1",
            provider="gcp",
            capacity=100.0,
            load=33.0,
            latency_ms=8.0,
        ),
        TopologyNode(
            id="node-azure-1",
            kind="vm",
            region="eastus",
            provider="azure",
            capacity=100.0,
            load=44.0,
            latency_ms=7.0,
        ),
        TopologyNode(
            id="edge-gw-1",
            kind="gateway",
            region="ap-south-1",
            provider="edge",
            capacity=50.0,
            load=22.0,
            latency_ms=28.0,
        ),
    )
    regions = tuple(sorted({n.region for n in nodes}))
    resources = tuple(sorted(f"{n.provider}:{n.kind}:{n.id}" for n in nodes))
    return InfrastructureSnapshot(
        id=_new_id("live"),
        timestamp=moment,
        topology=nodes,
        resources=resources,
        regions=regions,
    )


def from_cloud_snapshot(
    cloud: CloudSnapshot,
    *,
    timestamp: datetime | None = None,
) -> InfrastructureSnapshot:
    """Project a cloud federation census into a twin snapshot (read-only)."""

    moment = timestamp or cloud.timestamp
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    nodes: list[TopologyNode] = []
    for resource in cloud.resources:
        nodes.append(_resource_to_node(resource))
    # Ensure at least region labels from providers when resources empty.
    regions = tuple(
        sorted(
            {
                *(n.region for n in nodes),
                *(p.region for p in cloud.providers),
            }
        )
    )
    resources = tuple(sorted(f"{r.provider}:{r.type}:{r.id}" for r in cloud.resources))
    return InfrastructureSnapshot(
        id=_new_id("fed"),
        timestamp=moment,
        topology=tuple(nodes),
        resources=resources,
        regions=regions,
    )


def _resource_to_node(resource: CloudResource) -> TopologyNode:
    meta = dict(resource.metadata)
    load = float(meta.get("load", 40.0))
    capacity = float(meta.get("capacity", 100.0))
    latency = float(meta.get("latency_ms", 5.0))
    available = bool(meta.get("available", True))
    return TopologyNode(
        id=resource.id,
        kind=resource.type,
        region=resource.region,
        provider=resource.provider,
        capacity=capacity,
        load=max(0.0, min(100.0, load)),
        latency_ms=max(0.0, latency),
        available=available,
        metadata=meta,
    )


def content_fingerprint(snapshot: InfrastructureSnapshot) -> str:
    """Stable content digest for twin snapshots (not a cloud API call)."""

    payload = "|".join(
        sorted(
            f"{n.id}:{n.available}:{n.load}:{n.latency_ms}" for n in snapshot.topology
        )
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
