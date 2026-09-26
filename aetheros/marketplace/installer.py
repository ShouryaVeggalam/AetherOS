"""Marketplace installer — install / uninstall / enable / disable / verify.

Copies plugin packages into a local install root after validation.
Never grants WRITE permissions. Never mutates core intelligence modules.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from aetheros.marketplace.models import InstalledPlugin, PluginManifest
from aetheros.marketplace.registry import MarketplaceRegistry
from aetheros.marketplace.validator import ValidationResult, validate_package


@dataclass
class MarketplaceInstaller:
    """Lifecycle operations over a local marketplace registry.

    Args:
        registry: Catalog + install-state store.
        install_root: Directory where verified packages are copied.
    """

    registry: MarketplaceRegistry
    install_root: Path = field(
        default_factory=lambda: Path("data/marketplace/installed")
    )

    def __post_init__(self) -> None:
        self.install_root = Path(self.install_root)

    def verify(self, source: Path | str) -> ValidationResult:
        """Validate a package path (manifest, checksum, SDK, permissions)."""

        source_path = Path(source)
        catalog = None
        # Prefer catalog entry when id can be inferred.
        result = validate_package(source_path)
        if result.manifest is not None:
            catalog = self.registry.get_plugin(result.manifest.id)
        if catalog is not None:
            return validate_package(source_path, expected=catalog)
        return result

    def install(self, source: Path | str, *, enable: bool = True) -> InstalledPlugin:
        """Validate, copy, and register a plugin package.

        Raises:
            ValueError: When validation fails or the package is incompatible.
        """

        source_path = Path(source)
        result = self.verify(source_path)
        if not result.ok or result.manifest is None:
            detail = "; ".join(result.reasons) or "validation failed"
            raise ValueError(f"install rejected: {detail}")

        manifest = result.manifest
        # Ensure catalog knows about this plugin.
        if self.registry.get_plugin(manifest.id) is None:
            self.registry.register(manifest)

        target = self.install_root / manifest.id
        if target.exists():
            shutil.rmtree(target)
        self.install_root.mkdir(parents=True, exist_ok=True)
        if source_path.is_dir():
            shutil.copytree(source_path, target)
        else:
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target / source_path.name)

        # Persist resolved marketplace metadata beside the package.
        meta = target / "marketplace.json"
        payload = manifest.to_dict()
        # Refresh checksum to match installed tree (excluding marketplace.json).
        from aetheros.marketplace.validator import compute_checksum_excluding

        payload["checksum"] = compute_checksum_excluding(
            target, exclude_names={"marketplace.json"}
        )
        meta.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        resolved = PluginManifest.from_dict(payload)

        record = InstalledPlugin(
            manifest=resolved,
            enabled=enable,
            installed_at=datetime.now(UTC),
            update_available=False,
            install_path=str(target),
        )
        return self.registry.put_installed(record)

    def uninstall(self, plugin_id: str) -> bool:
        """Remove an installed plugin package and state entry."""

        record = self.registry.get_installed(plugin_id)
        if record is None:
            return False
        path = (
            Path(record.install_path)
            if record.install_path
            else self.install_root / plugin_id
        )
        if path.exists():
            shutil.rmtree(path)
        return self.registry.remove_installed(plugin_id)

    def enable(self, plugin_id: str) -> InstalledPlugin:
        """Mark an installed plugin as enabled (sandbox still applies)."""

        record = self.registry.get_installed(plugin_id)
        if record is None:
            raise KeyError(f"plugin not installed: {plugin_id}")
        updated = InstalledPlugin(
            manifest=record.manifest,
            enabled=True,
            installed_at=record.installed_at,
            update_available=record.update_available,
            install_path=record.install_path,
        )
        return self.registry.put_installed(updated)

    def disable(self, plugin_id: str) -> InstalledPlugin:
        """Mark an installed plugin as disabled."""

        record = self.registry.get_installed(plugin_id)
        if record is None:
            raise KeyError(f"plugin not installed: {plugin_id}")
        updated = InstalledPlugin(
            manifest=record.manifest,
            enabled=False,
            installed_at=record.installed_at,
            update_available=record.update_available,
            install_path=record.install_path,
        )
        return self.registry.put_installed(updated)
