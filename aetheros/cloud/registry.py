"""Cloud Federation Registry — observed provider index (no credentials).

Tracks connected providers, regions, API versions, snapshot age, and health.
Never stores secrets, tokens, kubeconfigs, or cloud credentials.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aetheros.cloud.models import (
    CloudProvider,
    CloudResource,
    FederationHealth,
    ProviderRecord,
    ProviderStatus,
)

DEFAULT_HEALTHY_AGE_SEC = 60.0
DEFAULT_DEGRADED_AGE_SEC = 300.0


class CloudRegistry:
    """In-memory registry of observed cloud providers."""

    def __init__(
        self,
        *,
        healthy_age_sec: float = DEFAULT_HEALTHY_AGE_SEC,
        degraded_age_sec: float = DEFAULT_DEGRADED_AGE_SEC,
    ) -> None:
        if healthy_age_sec <= 0 or degraded_age_sec <= 0:
            raise ValueError("age thresholds must be positive")
        if healthy_age_sec > degraded_age_sec:
            raise ValueError("healthy_age_sec must be <= degraded_age_sec")
        self._healthy_age = float(healthy_age_sec)
        self._degraded_age = float(degraded_age_sec)
        self._records: dict[str, ProviderRecord] = {}
        self._resources: dict[str, tuple[CloudResource, ...]] = {}

    def register(
        self,
        provider: CloudProvider,
        *,
        resources: tuple[CloudResource, ...] = (),
        now: datetime | None = None,
        status: ProviderStatus | None = None,
    ) -> ProviderRecord:
        """Upsert a provider observation (metadata only)."""

        moment = now or datetime.now(UTC)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        age = 0.0
        resolved: ProviderStatus
        if status is not None:
            resolved = status
        elif not provider.connected:
            resolved = "offline"
        else:
            resolved = "healthy"
        record = ProviderRecord(
            provider=provider,
            status=resolved,
            api_version=provider.version,
            snapshot_age_seconds=age,
            last_seen=moment,
            resource_count=len(resources),
        )
        self._records[provider.id] = record
        self._resources[provider.id] = tuple(resources)
        return record

    def get(self, provider_id: str) -> ProviderRecord | None:
        """Return one provider record or None."""

        return self._records.get(provider_id)

    def list_providers(self) -> tuple[ProviderRecord, ...]:
        """All known providers sorted by id."""

        return tuple(sorted(self._records.values(), key=lambda r: r.provider.id))

    def list_regions(self) -> tuple[str, ...]:
        """Distinct regions across registered providers and resources."""

        seen: set[str] = set()
        ordered: list[str] = []
        for record in self.list_providers():
            region = record.provider.region
            if region not in seen:
                seen.add(region)
                ordered.append(region)
        for resources in self._resources.values():
            for resource in resources:
                if resource.region not in seen:
                    seen.add(resource.region)
                    ordered.append(resource.region)
        return tuple(ordered)

    def resources_for(self, provider_id: str) -> tuple[CloudResource, ...]:
        """Resources last observed for one provider."""

        return self._resources.get(provider_id, ())

    def all_resources(self) -> tuple[CloudResource, ...]:
        """Flatten all observed resources (stable provider-id order)."""

        out: list[CloudResource] = []
        for record in self.list_providers():
            out.extend(self._resources.get(record.provider.id, ()))
        return tuple(out)

    def refresh_ages(self, *, now: datetime | None = None) -> None:
        """Recompute snapshot ages and health from last_seen."""

        moment = now or datetime.now(UTC)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        updated: dict[str, ProviderRecord] = {}
        for pid, record in self._records.items():
            last = record.last_seen
            if last.tzinfo is None:
                last = last.replace(tzinfo=UTC)
            age = max(0.0, (moment - last).total_seconds())
            if not record.provider.connected or age > self._degraded_age:
                status: ProviderStatus = "offline"
            elif age > self._healthy_age:
                status = "degraded"
            else:
                status = "healthy"
            updated[pid] = ProviderRecord(
                provider=record.provider,
                status=status,
                api_version=record.api_version,
                snapshot_age_seconds=age,
                last_seen=record.last_seen,
                resource_count=record.resource_count,
            )
        self._records = updated

    def health(self, *, now: datetime | None = None) -> FederationHealth:
        """Aggregate federation health with confidence in [0, 1]."""

        self.refresh_ages(now=now)
        online = degraded = offline = 0
        for record in self._records.values():
            if record.status == "healthy":
                online += 1
            elif record.status == "degraded":
                degraded += 1
            else:
                offline += 1
        total = online + degraded + offline
        if total == 0:
            return FederationHealth(online=0, degraded=0, offline=0, confidence=0.0)
        # Confidence weighted toward online providers.
        confidence = (online + 0.5 * degraded) / total
        return FederationHealth(
            online=online,
            degraded=degraded,
            offline=offline,
            confidence=round(confidence, 4),
        )

    def max_snapshot_age(self, *, now: datetime | None = None) -> float:
        """Oldest provider snapshot age in seconds."""

        self.refresh_ages(now=now)
        if not self._records:
            return 0.0
        return max(r.snapshot_age_seconds for r in self._records.values())
