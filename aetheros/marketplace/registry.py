"""Local Extension Marketplace registry — JSON index backed.

register / unregister / list / get. No remote server required.
Writes only marketplace index files under a data directory — never
mutates Resource Graph, Reasoning, Twin, Federation, or core runtime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from aetheros.marketplace.models import (
    InstalledPlugin,
    MarketplaceIndex,
    PluginManifest,
)


@dataclass
class MarketplaceRegistry:
    """Local plugin catalog + install-state registry.

    Args:
        root: Directory holding ``catalog.json`` and ``installed.json``.
    """

    root: Path = field(default_factory=lambda: Path("data/marketplace"))
    _catalog: dict[str, PluginManifest] = field(default_factory=dict, init=False)
    _installed: dict[str, InstalledPlugin] = field(default_factory=dict, init=False)
    _loaded: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    @property
    def catalog_path(self) -> Path:
        """Path to the published catalog JSON index."""

        return self.root / "catalog.json"

    @property
    def installed_path(self) -> Path:
        """Path to the local install-state JSON index."""

        return self.root / "installed.json"

    def ensure_loaded(self) -> None:
        """Load catalog + install state from disk once."""

        if self._loaded:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self._catalog = self._read_catalog()
        self._installed = self._read_installed()
        self._loaded = True

    def reload(self) -> None:
        """Force reload from disk."""

        self._loaded = False
        self.ensure_loaded()

    def register(self, manifest: PluginManifest) -> PluginManifest:
        """Add or replace a catalog entry and persist the index."""

        self.ensure_loaded()
        self._catalog[manifest.id] = manifest
        self._write_catalog()
        return manifest

    def unregister(self, plugin_id: str) -> bool:
        """Remove a catalog entry. Returns True when something was removed."""

        self.ensure_loaded()
        if plugin_id not in self._catalog:
            return False
        del self._catalog[plugin_id]
        self._write_catalog()
        return True

    def list_plugins(self) -> tuple[PluginManifest, ...]:
        """Return all catalog manifests (immutable tuple, sorted by id)."""

        self.ensure_loaded()
        return tuple(self._catalog[k] for k in sorted(self._catalog))

    def get_plugin(self, plugin_id: str) -> PluginManifest | None:
        """Return one catalog manifest or None."""

        self.ensure_loaded()
        return self._catalog.get(plugin_id)

    def list_installed(self) -> tuple[InstalledPlugin, ...]:
        """Return all install records (immutable, sorted by id)."""

        self.ensure_loaded()
        return tuple(self._installed[k] for k in sorted(self._installed))

    def get_installed(self, plugin_id: str) -> InstalledPlugin | None:
        """Return one install record or None."""

        self.ensure_loaded()
        return self._installed.get(plugin_id)

    def put_installed(self, record: InstalledPlugin) -> InstalledPlugin:
        """Upsert an install record and persist state."""

        self.ensure_loaded()
        self._installed[record.manifest.id] = record
        self._write_installed()
        return record

    def remove_installed(self, plugin_id: str) -> bool:
        """Remove an install record. Returns True when removed."""

        self.ensure_loaded()
        if plugin_id not in self._installed:
            return False
        del self._installed[plugin_id]
        self._write_installed()
        return True

    def index(self) -> MarketplaceIndex:
        """Build an immutable MarketplaceIndex snapshot."""

        self.ensure_loaded()
        return MarketplaceIndex(
            plugins=self.list_plugins(),
            sdk_version="5.0.0",
            generated_at=datetime.now(UTC),
        )

    def _read_catalog(self) -> dict[str, PluginManifest]:
        if not self.catalog_path.is_file():
            return {}
        raw = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        plugins = raw.get("plugins") or []
        out: dict[str, PluginManifest] = {}
        if isinstance(plugins, list):
            for item in plugins:
                if isinstance(item, dict):
                    manifest = PluginManifest.from_dict(item)
                    out[manifest.id] = manifest
        return out

    def _write_catalog(self) -> None:
        index = MarketplaceIndex(
            plugins=tuple(self._catalog[k] for k in sorted(self._catalog)),
            sdk_version="5.0.0",
            generated_at=datetime.now(UTC),
        )
        self.root.mkdir(parents=True, exist_ok=True)
        self.catalog_path.write_text(
            json.dumps(index.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _read_installed(self) -> dict[str, InstalledPlugin]:
        if not self.installed_path.is_file():
            return {}
        raw = json.loads(self.installed_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        items = raw.get("installed") or []
        out: dict[str, InstalledPlugin] = {}
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    record = InstalledPlugin.from_dict(item)
                    out[record.manifest.id] = record
        return out

    def _write_installed(self) -> None:
        payload = {
            "installed": [self._installed[k].to_dict() for k in sorted(self._installed)]
        }
        self.root.mkdir(parents=True, exist_ok=True)
        self.installed_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
