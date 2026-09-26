"""Marketplace updater — recommendations only (never auto-updates).

Detects newer catalog versions, SDK incompatibility, and deprecations.
Operators decide whether to install an update.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.marketplace.models import PluginManifest
from aetheros.marketplace.registry import MarketplaceRegistry

try:
    from plugins.sdk.manifest import sdk_constraint_allows
except Exception:  # pragma: no cover

    def sdk_constraint_allows(constraint: str, *, major: int = 5) -> bool:
        return str(major) in constraint


@dataclass(frozen=True, slots=True)
class UpdateRecommendation:
    """Immutable update advice for one installed plugin."""

    plugin_id: str
    current_version: str
    available_version: str | None
    update_available: bool
    sdk_compatible: bool
    deprecated: bool
    reason: str


def _version_tuple(version: str) -> tuple[int, ...]:
    """Parse a dotted version into a comparable int tuple."""

    parts: list[int] = []
    for token in version.strip().split("."):
        digits = "".join(ch for ch in token if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def is_newer(candidate: str, current: str) -> bool:
    """Return True when ``candidate`` is a newer semver-ish version."""

    return _version_tuple(candidate) > _version_tuple(current)


class MarketplaceUpdater:
    """Compare installed plugins against the local catalog."""

    def __init__(self, registry: MarketplaceRegistry) -> None:
        self._registry = registry

    def check(self, plugin_id: str) -> UpdateRecommendation:
        """Return update advice for one installed plugin."""

        installed = self._registry.get_installed(plugin_id)
        if installed is None:
            return UpdateRecommendation(
                plugin_id=plugin_id,
                current_version="",
                available_version=None,
                update_available=False,
                sdk_compatible=False,
                deprecated=False,
                reason="not installed",
            )
        catalog = self._registry.get_plugin(plugin_id)
        return self._advise(installed.manifest, catalog)

    def check_all(self) -> tuple[UpdateRecommendation, ...]:
        """Return recommendations for every installed plugin."""

        return tuple(
            self._advise(record.manifest, self._registry.get_plugin(record.manifest.id))
            for record in self._registry.list_installed()
        )

    def mark_update_flags(self) -> tuple[UpdateRecommendation, ...]:
        """Refresh ``update_available`` flags on install records (no package replace)."""

        from aetheros.marketplace.models import InstalledPlugin

        advice = self.check_all()
        by_id = {item.plugin_id: item for item in advice}
        for record in self._registry.list_installed():
            tip = by_id.get(record.manifest.id)
            flag = bool(tip and tip.update_available and tip.sdk_compatible)
            if record.update_available != flag:
                self._registry.put_installed(
                    InstalledPlugin(
                        manifest=record.manifest,
                        enabled=record.enabled,
                        installed_at=record.installed_at,
                        update_available=flag,
                        install_path=record.install_path,
                    )
                )
        return advice

    def _advise(
        self,
        installed: PluginManifest,
        catalog: PluginManifest | None,
    ) -> UpdateRecommendation:
        if catalog is None:
            return UpdateRecommendation(
                plugin_id=installed.id,
                current_version=installed.version,
                available_version=None,
                update_available=False,
                sdk_compatible=sdk_constraint_allows(installed.sdk_version),
                deprecated=True,
                reason="removed from catalog (deprecated)",
            )
        compatible = sdk_constraint_allows(catalog.sdk_version)
        newer = is_newer(catalog.version, installed.version)
        if newer and not compatible:
            return UpdateRecommendation(
                plugin_id=installed.id,
                current_version=installed.version,
                available_version=catalog.version,
                update_available=True,
                sdk_compatible=False,
                deprecated=False,
                reason="newer version requires incompatible SDK — do not auto-update",
            )
        if newer:
            return UpdateRecommendation(
                plugin_id=installed.id,
                current_version=installed.version,
                available_version=catalog.version,
                update_available=True,
                sdk_compatible=True,
                deprecated=False,
                reason="newer version available — install manually",
            )
        if not compatible:
            return UpdateRecommendation(
                plugin_id=installed.id,
                current_version=installed.version,
                available_version=catalog.version,
                update_available=False,
                sdk_compatible=False,
                deprecated=False,
                reason="installed plugin SDK constraint incompatible with host",
            )
        return UpdateRecommendation(
            plugin_id=installed.id,
            current_version=installed.version,
            available_version=catalog.version,
            update_available=False,
            sdk_compatible=True,
            deprecated=False,
            reason="up to date",
        )
