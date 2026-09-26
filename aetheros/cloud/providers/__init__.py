"""Cloud provider adapters — read-only observation only.

Each adapter normalizes inventory into ``CloudResource`` records.
Adapters never call provision / delete / restart / mutate APIs.
Credentials are never accepted or stored.
"""

from __future__ import annotations

from aetheros.cloud.providers.aws import AWSProvider
from aetheros.cloud.providers.azure import AzureProvider
from aetheros.cloud.providers.docker import DockerProvider
from aetheros.cloud.providers.edge import EdgeProvider
from aetheros.cloud.providers.gcp import GCPProvider
from aetheros.cloud.providers.kubernetes import KubernetesProvider

__all__ = [
    "AWSProvider",
    "AzureProvider",
    "DockerProvider",
    "EdgeProvider",
    "GCPProvider",
    "KubernetesProvider",
]
