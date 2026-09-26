"""Cloud Federation Engine — v6.0 P1 read-only multi-cloud observation.

Unified federation layer for AWS, Azure, GCP, Kubernetes, Docker, and Edge.
Observation, reasoning inputs, and simulation only — never provision,
delete, restart, or modify cloud resources. No Terraform. No kubectl.
"""

from __future__ import annotations

from aetheros.cloud.federation import (
    CloudFederationEngine,
    FederationView,
    seed_demo_cloud,
)
from aetheros.cloud.formatter import CloudFederationPanel
from aetheros.cloud.models import (
    PROVIDER_AWS,
    PROVIDER_AZURE,
    PROVIDER_DOCKER,
    PROVIDER_EDGE,
    PROVIDER_GCP,
    PROVIDER_IDS,
    PROVIDER_KUBERNETES,
    RESOURCE_TYPES,
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
from aetheros.cloud.registry import (
    DEFAULT_DEGRADED_AGE_SEC,
    DEFAULT_HEALTHY_AGE_SEC,
    CloudRegistry,
)
from aetheros.cloud.serializer import (
    decode_snapshot,
    dumps_canonical,
    encode_snapshot,
    snapshot_to_json,
)
from aetheros.cloud.snapshot import (
    SnapshotDiff,
    capture,
    compare,
    deserialize,
    hash_snapshot,
    serialize,
    topology_hash,
)

__all__ = [
    "AWSProvider",
    "AzureProvider",
    "CloudFederationEngine",
    "CloudFederationPanel",
    "CloudProvider",
    "CloudRegistry",
    "CloudResource",
    "DEFAULT_DEGRADED_AGE_SEC",
    "DEFAULT_HEALTHY_AGE_SEC",
    "DockerProvider",
    "EdgeProvider",
    "FederationHealth",
    "FederationView",
    "GCPProvider",
    "InfrastructureSnapshot",
    "KubernetesProvider",
    "PROVIDER_AWS",
    "PROVIDER_AZURE",
    "PROVIDER_DOCKER",
    "PROVIDER_EDGE",
    "PROVIDER_GCP",
    "PROVIDER_IDS",
    "PROVIDER_KUBERNETES",
    "ProviderRecord",
    "RESOURCE_TYPES",
    "SnapshotDiff",
    "capture",
    "compare",
    "decode_snapshot",
    "deserialize",
    "dumps_canonical",
    "encode_snapshot",
    "hash_snapshot",
    "seed_demo_cloud",
    "serialize",
    "snapshot_to_json",
    "topology_hash",
]
