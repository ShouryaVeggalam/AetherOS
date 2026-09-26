"""Cloud Federation models — immutable, read-only infrastructure contracts.

v6.0 P1. Normalized representation of multi-cloud inventory. Never stores
credentials. Never represents provision / delete / restart / mutate actions.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

PROVIDER_AWS = "aws"
PROVIDER_AZURE = "azure"
PROVIDER_GCP = "gcp"
PROVIDER_KUBERNETES = "kubernetes"
PROVIDER_DOCKER = "docker"
PROVIDER_EDGE = "edge"

PROVIDER_IDS: frozenset[str] = frozenset(
    {
        PROVIDER_AWS,
        PROVIDER_AZURE,
        PROVIDER_GCP,
        PROVIDER_KUBERNETES,
        PROVIDER_DOCKER,
        PROVIDER_EDGE,
    }
)

# Normalized resource type tokens (provider-prefixed for clarity).
RESOURCE_TYPES: frozenset[str] = frozenset(
    {
        # AWS
        "ec2",
        "ebs",
        "vpc",
        "rds",
        # Azure
        "vm",
        "storage",
        "network",
        # GCP
        "compute",
        "disk",
        # Kubernetes
        "cluster",
        "node",
        "pod",
        "service",
        # Docker
        "container",
        "image",
        # Edge
        "device",
        "gateway",
    }
)

HealthLabel = Literal["online", "degraded", "offline"]
ProviderStatus = Literal["healthy", "degraded", "offline", "unknown"]


@dataclass(frozen=True, slots=True)
class CloudProvider:
    """One connected (observed) cloud / runtime provider endpoint.

    Attributes:
        id: Stable provider instance id (e.g. ``aws-us-east-1``).
        name: Human label (e.g. ``AWS``).
        version: Observed API / control-plane version string.
        region: Primary region or ``global``.
        connected: Whether the last observation succeeded (read-only).
    """

    id: str
    name: str
    version: str
    region: str
    connected: bool = True

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        if not self.version.strip():
            raise ValueError("version must be non-empty")
        if not self.region.strip():
            raise ValueError("region must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export (never includes credentials)."""

        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "region": self.region,
            "connected": self.connected,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CloudProvider:
        """Parse a CloudProvider from a mapping."""

        return cls(
            id=str(data.get("id") or "").strip(),
            name=str(data.get("name") or "").strip(),
            version=str(data.get("version") or "").strip(),
            region=str(data.get("region") or "").strip(),
            connected=bool(data.get("connected", True)),
        )


@dataclass(frozen=True, slots=True)
class CloudResource:
    """Normalized infrastructure resource across all providers."""

    id: str
    provider: str
    type: str
    name: str
    region: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.provider.strip():
            raise ValueError("provider must be non-empty")
        if not self.type.strip():
            raise ValueError("type must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        if not self.region.strip():
            raise ValueError("region must be non-empty")
        # Freeze nested mapping.
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "id": self.id,
            "provider": self.provider,
            "type": self.type,
            "name": self.name,
            "region": self.region,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CloudResource:
        """Parse a CloudResource from a mapping."""

        meta = data.get("metadata") or {}
        if not isinstance(meta, Mapping):
            raise ValueError("metadata must be a mapping")
        return cls(
            id=str(data.get("id") or "").strip(),
            provider=str(data.get("provider") or "").strip(),
            type=str(data.get("type") or "").strip(),
            name=str(data.get("name") or "").strip(),
            region=str(data.get("region") or "").strip(),
            metadata=dict(meta),
        )


@dataclass(frozen=True, slots=True)
class InfrastructureSnapshot:
    """Immutable multi-provider infrastructure census."""

    timestamp: datetime
    providers: tuple[CloudProvider, ...]
    resources: tuple[CloudResource, ...]
    topology_hash: str

    def __post_init__(self) -> None:
        if not self.topology_hash.strip():
            raise ValueError("topology_hash must be non-empty")
        object.__setattr__(self, "providers", tuple(self.providers))
        object.__setattr__(self, "resources", tuple(self.resources))

    @property
    def provider_count(self) -> int:
        """Number of providers in this snapshot."""

        return len(self.providers)

    @property
    def resource_count(self) -> int:
        """Number of resources in this snapshot."""

        return len(self.resources)

    @property
    def regions(self) -> tuple[str, ...]:
        """Distinct region labels across providers and resources."""

        seen: set[str] = set()
        ordered: list[str] = []
        for p in self.providers:
            if p.region not in seen:
                seen.add(p.region)
                ordered.append(p.region)
        for r in self.resources:
            if r.region not in seen:
                seen.add(r.region)
                ordered.append(r.region)
        return tuple(ordered)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export (no pickle)."""

        return {
            "timestamp": self.timestamp.isoformat(),
            "providers": [p.to_dict() for p in self.providers],
            "resources": [r.to_dict() for r in self.resources],
            "topology_hash": self.topology_hash,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> InfrastructureSnapshot:
        """Parse an InfrastructureSnapshot from a mapping."""

        providers_raw = data.get("providers") or ()
        resources_raw = data.get("resources") or ()
        if not isinstance(providers_raw, (list, tuple)):
            raise ValueError("providers must be a list")
        if not isinstance(resources_raw, (list, tuple)):
            raise ValueError("resources must be a list")
        return cls(
            timestamp=datetime.fromisoformat(str(data.get("timestamp") or "")),
            providers=tuple(CloudProvider.from_dict(p) for p in providers_raw),
            resources=tuple(CloudResource.from_dict(r) for r in resources_raw),
            topology_hash=str(data.get("topology_hash") or "").strip(),
        )


@dataclass(frozen=True, slots=True)
class FederationHealth:
    """Aggregate health of the cloud federation surface."""

    online: int
    degraded: int
    offline: int
    confidence: float

    def __post_init__(self) -> None:
        if self.online < 0 or self.degraded < 0 or self.offline < 0:
            raise ValueError("counts must be non-negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")

    @property
    def total(self) -> int:
        """Total providers counted."""

        return self.online + self.degraded + self.offline

    @property
    def label(self) -> HealthLabel:
        """Coarse federation label for UI."""

        if self.offline == 0 and self.degraded == 0 and self.online > 0:
            return "online"
        if self.online == 0 and self.degraded == 0:
            return "offline"
        return "degraded"

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "online": self.online,
            "degraded": self.degraded,
            "offline": self.offline,
            "confidence": self.confidence,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> FederationHealth:
        """Parse FederationHealth from a mapping."""

        return cls(
            online=int(data.get("online") or 0),
            degraded=int(data.get("degraded") or 0),
            offline=int(data.get("offline") or 0),
            confidence=float(data.get("confidence") or 0.0),
        )


@dataclass(frozen=True, slots=True)
class ProviderRecord:
    """Registry row for one observed provider (no credentials)."""

    provider: CloudProvider
    status: ProviderStatus
    api_version: str
    snapshot_age_seconds: float
    last_seen: datetime
    resource_count: int = 0

    def __post_init__(self) -> None:
        if self.status not in ("healthy", "degraded", "offline", "unknown"):
            raise ValueError(f"invalid status: {self.status}")
        if self.snapshot_age_seconds < 0:
            raise ValueError("snapshot_age_seconds must be non-negative")
        if self.resource_count < 0:
            raise ValueError("resource_count must be non-negative")
        if not self.api_version.strip():
            raise ValueError("api_version must be non-empty")
