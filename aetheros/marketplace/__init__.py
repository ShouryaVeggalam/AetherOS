"""Extension Marketplace — v5.0 P3 discovery and lifecycle layer.

Local JSON catalog · sandboxed install · read-only permissions.
Does not modify Resource Graph, Reasoning, Twin, Federation, or core runtime.
"""

from __future__ import annotations

from aetheros.marketplace.demo import demo_catalog, seed_demo_marketplace
from aetheros.marketplace.discovery import DiscoveryQuery, MarketplaceDiscovery
from aetheros.marketplace.formatter import MarketplacePanel
from aetheros.marketplace.installer import MarketplaceInstaller
from aetheros.marketplace.models import (
    InstalledPlugin,
    MarketplaceIndex,
    PluginManifest,
)
from aetheros.marketplace.permissions import (
    ALLOWED_PERMISSIONS,
    PERMISSION_TO_CAPABILITY,
    READ_CONTEXT,
    READ_GRAPH,
    READ_RESEARCH,
    READ_SIMULATION,
    READ_TELEMETRY,
    is_write_permission,
    normalize_permission,
    to_sdk_capabilities,
    validate_permissions,
)
from aetheros.marketplace.registry import MarketplaceRegistry
from aetheros.marketplace.updater import (
    MarketplaceUpdater,
    UpdateRecommendation,
    is_newer,
)
from aetheros.marketplace.validator import (
    ValidationResult,
    compute_checksum,
    compute_checksum_excluding,
    validate_manifest,
    validate_package,
)

__all__ = [
    "ALLOWED_PERMISSIONS",
    "DiscoveryQuery",
    "InstalledPlugin",
    "MarketplaceDiscovery",
    "MarketplaceIndex",
    "MarketplaceInstaller",
    "MarketplacePanel",
    "MarketplaceRegistry",
    "MarketplaceUpdater",
    "PERMISSION_TO_CAPABILITY",
    "PluginManifest",
    "READ_CONTEXT",
    "READ_GRAPH",
    "READ_RESEARCH",
    "READ_SIMULATION",
    "READ_TELEMETRY",
    "UpdateRecommendation",
    "ValidationResult",
    "compute_checksum",
    "compute_checksum_excluding",
    "demo_catalog",
    "is_newer",
    "is_write_permission",
    "normalize_permission",
    "seed_demo_marketplace",
    "to_sdk_capabilities",
    "validate_manifest",
    "validate_package",
    "validate_permissions",
]
