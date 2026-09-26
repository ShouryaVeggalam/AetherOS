"""Cloud Federation Engine — unified read-only multi-cloud observation.

Ingests provider inventories into a registry and produces immutable
infrastructure snapshots. Never provisions, deletes, restarts, or modifies
cloud resources. No Terraform. No kubectl. No cloud mutations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aetheros.cloud.models import (
    CloudProvider,
    CloudResource,
    FederationHealth,
    InfrastructureSnapshot,
    ProviderRecord,
)
from aetheros.cloud.providers import (
    AWSProvider,
    AzureProvider,
    DockerProvider,
    EdgeProvider,
    GCPProvider,
    KubernetesProvider,
)
from aetheros.cloud.registry import CloudRegistry
from aetheros.cloud.snapshot import (
    SnapshotDiff,
    capture,
    compare,
    hash_snapshot,
    serialize,
)


@dataclass(frozen=True, slots=True)
class FederationView:
    """Immutable operator view of the federation surface."""

    snapshot: InfrastructureSnapshot
    health: FederationHealth
    records: tuple[ProviderRecord, ...]
    snapshot_age_seconds: float


class CloudFederationEngine:
    """Orchestrate provider observation → registry → immutable snapshots."""

    def __init__(self, registry: CloudRegistry | None = None) -> None:
        self.registry = registry or CloudRegistry()
        self._last: InfrastructureSnapshot | None = None

    @property
    def last_snapshot(self) -> InfrastructureSnapshot | None:
        """Most recent captured snapshot, if any."""

        return self._last

    def ingest_provider(
        self,
        adapter: Any,
        inventory: Sequence[Mapping[str, Any]] | None = None,
        *,
        now: datetime | None = None,
    ) -> ProviderRecord:
        """Observe one provider adapter and register its resources."""

        provider: CloudProvider = adapter.provider
        resources: tuple[CloudResource, ...] = adapter.observe(inventory)
        return self.registry.register(provider, resources=resources, now=now)

    def capture_all(
        self,
        *,
        now: datetime | None = None,
        inventories: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
        use_demo: bool = True,
    ) -> InfrastructureSnapshot:
        """Observe all built-in providers and capture an immutable snapshot.

        When ``use_demo`` is True and no per-provider inventory is supplied,
        each adapter uses its static demo inventory (dashboard seeding).
        """

        inventories = inventories or {}
        adapters = [
            AWSProvider(),
            AzureProvider(),
            GCPProvider(),
            KubernetesProvider(),
            DockerProvider(),
            EdgeProvider(),
        ]
        for adapter in adapters:
            inv = inventories.get(adapter.kind)
            if inv is None and not use_demo:
                inv = ()
            self.ingest_provider(adapter, inv, now=now)

        providers = tuple(r.provider for r in self.registry.list_providers())
        resources = self.registry.all_resources()
        snap = capture(providers, resources, timestamp=now)
        self._last = snap
        return snap

    def view(self, *, now: datetime | None = None) -> FederationView:
        """Build an operator view from the registry + last snapshot."""

        if self._last is None:
            self.capture_all(now=now)
        assert self._last is not None
        health = self.registry.health(now=now)
        return FederationView(
            snapshot=self._last,
            health=health,
            records=self.registry.list_providers(),
            snapshot_age_seconds=self.registry.max_snapshot_age(now=now),
        )

    def serialize_last(self, *, pretty: bool = True) -> str:
        """JSON-export the last snapshot (empty object if none)."""

        if self._last is None:
            return "{}"
        return serialize(self._last, pretty=pretty)

    def compare_with(self, other: InfrastructureSnapshot) -> SnapshotDiff:
        """Diff the last snapshot against another (requires a prior capture)."""

        if self._last is None:
            raise RuntimeError("no snapshot captured yet")
        return compare(self._last, other)

    def verify_hash(self) -> bool:
        """True when last snapshot topology_hash matches recomputation."""

        if self._last is None:
            return False
        return hash_snapshot(self._last) == self._last.topology_hash


def seed_demo_cloud(
    engine: CloudFederationEngine | None = None,
    *,
    now: datetime | None = None,
) -> CloudFederationEngine:
    """Seed a demo multi-cloud federation for the dashboard."""

    eng = engine or CloudFederationEngine()
    eng.capture_all(now=now, use_demo=True)
    return eng
