"""Marketplace data models — immutable catalog and install records.

Discovery / lifecycle metadata only. Never executes plugin code.
Does not modify Resource Graph, Reasoning, Twin, Federation, or core runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PluginManifest:
    """Published plugin identity for the Extension Marketplace.

    Attributes:
        id: Stable plugin identifier (kebab-case).
        name: Human-readable display name.
        version: Plugin semantic version string.
        author: Author or organization.
        description: Short summary.
        sdk_version: Declared Plugin SDK constraint (e.g. ``>=5.0.0,<6``).
        category: Marketplace category label.
        permissions: Requested read-only permission names.
        checksum: Content integrity digest (``sha256:<hex>``).
    """

    id: str
    name: str
    version: str
    author: str
    description: str
    sdk_version: str
    category: str
    permissions: tuple[str, ...]
    checksum: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")
        if not self.version.strip():
            raise ValueError("version must be non-empty")
        if not self.checksum.strip():
            raise ValueError("checksum must be non-empty")

    def to_dict(self) -> dict[str, object]:
        """Serialize for JSON index persistence."""

        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "sdk_version": self.sdk_version,
            "category": self.category,
            "permissions": list(self.permissions),
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> PluginManifest:
        """Build a manifest from a JSON-compatible mapping."""

        perms = data.get("permissions") or ()
        if isinstance(perms, str):
            perms = [perms]
        if not isinstance(perms, (list, tuple)):
            raise ValueError("permissions must be a list")
        return cls(
            id=str(data.get("id") or "").strip(),
            name=str(data.get("name") or "").strip(),
            version=str(data.get("version") or "").strip(),
            author=str(data.get("author") or "unknown").strip(),
            description=str(data.get("description") or "").strip(),
            sdk_version=str(data.get("sdk_version") or ">=5.0.0,<6").strip(),
            category=str(data.get("category") or "general").strip(),
            permissions=tuple(str(p).strip() for p in perms if str(p).strip()),
            checksum=str(data.get("checksum") or "").strip(),
        )


@dataclass(frozen=True, slots=True)
class InstalledPlugin:
    """Local install record for one marketplace plugin."""

    manifest: PluginManifest
    enabled: bool
    installed_at: datetime
    update_available: bool = False
    install_path: str = ""

    def to_dict(self) -> dict[str, object]:
        """Serialize for JSON state persistence."""

        return {
            "manifest": self.manifest.to_dict(),
            "enabled": self.enabled,
            "installed_at": self.installed_at.isoformat(),
            "update_available": self.update_available,
            "install_path": self.install_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> InstalledPlugin:
        """Build an install record from a JSON-compatible mapping."""

        raw_manifest = data.get("manifest")
        if not isinstance(raw_manifest, dict):
            raise ValueError("installed plugin requires manifest object")
        stamp = str(data.get("installed_at") or "")
        installed_at = datetime.fromisoformat(stamp)
        return cls(
            manifest=PluginManifest.from_dict(raw_manifest),
            enabled=bool(data.get("enabled", True)),
            installed_at=installed_at,
            update_available=bool(data.get("update_available", False)),
            install_path=str(data.get("install_path") or ""),
        )


@dataclass(frozen=True, slots=True)
class MarketplaceIndex:
    """Immutable catalog snapshot persisted as a JSON index."""

    plugins: tuple[PluginManifest, ...]
    sdk_version: str
    generated_at: datetime

    def to_dict(self) -> dict[str, object]:
        """Serialize the full catalog index."""

        return {
            "plugins": [p.to_dict() for p in self.plugins],
            "sdk_version": self.sdk_version,
            "generated_at": self.generated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> MarketplaceIndex:
        """Parse a catalog index mapping."""

        raw_plugins = data.get("plugins") or ()
        if not isinstance(raw_plugins, list):
            raise ValueError("plugins must be a list")
        plugins = tuple(
            PluginManifest.from_dict(item)
            for item in raw_plugins
            if isinstance(item, dict)
        )
        stamp = str(data.get("generated_at") or "")
        return cls(
            plugins=plugins,
            sdk_version=str(data.get("sdk_version") or "5.0.0"),
            generated_at=datetime.fromisoformat(stamp),
        )
