"""Demo catalog seed for the Extension Marketplace dashboard panel.

Presentation-only fixtures. Never loads unrestricted plugin code into core.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from aetheros.marketplace.installer import MarketplaceInstaller
from aetheros.marketplace.models import InstalledPlugin, PluginManifest
from aetheros.marketplace.permissions import (
    READ_CONTEXT,
    READ_GRAPH,
    READ_RESEARCH,
    READ_SIMULATION,
    READ_TELEMETRY,
)
from aetheros.marketplace.registry import MarketplaceRegistry
from aetheros.marketplace.updater import MarketplaceUpdater


def demo_catalog() -> tuple[PluginManifest, ...]:
    """Return a frozen demo catalog (includes NVIDIA Intelligence highlight)."""

    return (
        PluginManifest(
            id="nvidia-intelligence",
            name="NVIDIA Intelligence",
            version="1.3.0",
            author="NVIDIA",
            description="GPU-aware insight plugin (read-only telemetry + graph).",
            sdk_version=">=5.0.0,<6",
            category="telemetry",
            permissions=(READ_GRAPH, READ_TELEMETRY),
            checksum="sha256:" + ("a" * 64),
        ),
        PluginManifest(
            id="hello-insight",
            name="Hello Insight",
            version="0.1.0",
            author="AetherOS Examples",
            description="Example sandboxed insight plugin for the v5 Plugin SDK.",
            sdk_version=">=5.0.0,<6",
            category="insight",
            permissions=(READ_GRAPH, READ_CONTEXT),
            checksum="sha256:" + ("b" * 64),
        ),
        PluginManifest(
            id="research-lens",
            name="Research Lens",
            version="2.0.1",
            author="Aether Labs",
            description="Research-grade observation summarizer.",
            sdk_version=">=5.0.0,<6",
            category="research",
            permissions=(READ_RESEARCH, READ_CONTEXT),
            checksum="sha256:" + ("c" * 64),
        ),
        PluginManifest(
            id="twin-scout",
            name="Twin Scout",
            version="0.9.0",
            author="SimOps",
            description="Digital Twin simulation advisor (read-only).",
            sdk_version=">=5.0.0,<6",
            category="simulation",
            permissions=(READ_SIMULATION, READ_GRAPH),
            checksum="sha256:" + ("d" * 64),
        ),
        PluginManifest(
            id="legacy-scout",
            name="Legacy Scout",
            version="0.2.0",
            author="Archive",
            description="Deprecated sample — SDK major 4 only.",
            sdk_version=">=4.0.0,<5",
            category="legacy",
            permissions=(READ_GRAPH,),
            checksum="sha256:" + ("e" * 64),
        ),
    )


def seed_demo_marketplace(
    registry: MarketplaceRegistry,
    *,
    install_root: Path | None = None,
) -> MarketplaceRegistry:
    """Populate catalog + a few installed records for dashboard demo.

    Does not copy real packages — installs metadata-only records suitable for
    Rich presentation. Update flags are refreshed via MarketplaceUpdater.
    """

    for manifest in demo_catalog():
        registry.register(manifest)

    # Register a newer catalog version for hello-insight to surface Updates.
    newer = PluginManifest(
        id="hello-insight",
        name="Hello Insight",
        version="0.2.0",
        author="AetherOS Examples",
        description="Example sandboxed insight plugin for the v5 Plugin SDK.",
        sdk_version=">=5.0.0,<6",
        category="insight",
        permissions=(READ_GRAPH, READ_CONTEXT),
        checksum="sha256:" + ("f" * 64),
    )
    registry.register(newer)

    now = datetime.now(UTC)
    root = Path(install_root) if install_root else registry.root / "installed"
    samples = (
        ("nvidia-intelligence", "1.3.0", True),
        ("hello-insight", "0.1.0", True),
        ("research-lens", "2.0.1", True),
        ("twin-scout", "0.9.0", False),
    )
    catalog_by_id = {m.id: m for m in demo_catalog()}
    catalog_by_id["hello-insight"] = PluginManifest(
        id="hello-insight",
        name="Hello Insight",
        version="0.1.0",
        author="AetherOS Examples",
        description="Example sandboxed insight plugin for the v5 Plugin SDK.",
        sdk_version=">=5.0.0,<6",
        category="insight",
        permissions=(READ_GRAPH, READ_CONTEXT),
        checksum="sha256:" + ("b" * 64),
    )
    for plugin_id, version, enabled in samples:
        base = catalog_by_id[plugin_id]
        manifest = PluginManifest(
            id=base.id,
            name=base.name,
            version=version,
            author=base.author,
            description=base.description,
            sdk_version=base.sdk_version,
            category=base.category,
            permissions=base.permissions,
            checksum=base.checksum,
        )
        registry.put_installed(
            InstalledPlugin(
                manifest=manifest,
                enabled=enabled,
                installed_at=now,
                update_available=False,
                install_path=str(root / plugin_id),
            )
        )

    MarketplaceUpdater(registry).mark_update_flags()
    # Touch installer type so demo wiring stays import-stable for callers.
    _ = MarketplaceInstaller
    return registry
