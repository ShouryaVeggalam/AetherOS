"""Marketplace discovery — immutable filtered views over the local catalog.

Supports category / author / SDK version / installed / enabled filters.
Never mutates registry state.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.marketplace.models import InstalledPlugin, PluginManifest
from aetheros.marketplace.registry import MarketplaceRegistry


def _sdk_major(constraint: str) -> int | None:
    """Best-effort major version extraction from an SDK constraint string."""

    text = constraint.strip()
    for token in (
        text.replace("<", " ")
        .replace(">", " ")
        .replace("=", " ")
        .replace(",", " ")
        .split()
    ):
        token = token.strip()
        if not token:
            continue
        head = token.split(".", 1)[0]
        if head.isdigit():
            return int(head)
    return None


@dataclass(frozen=True, slots=True)
class DiscoveryQuery:
    """Immutable discovery filter set. Missing fields mean unrestricted."""

    category: str | None = None
    author: str | None = None
    sdk_version: str | None = None
    installed: bool | None = None
    enabled: bool | None = None


class MarketplaceDiscovery:
    """Read-only discovery facade over a ``MarketplaceRegistry``."""

    def __init__(self, registry: MarketplaceRegistry) -> None:
        self._registry = registry

    def search(self, query: DiscoveryQuery | None = None) -> tuple[PluginManifest, ...]:
        """Return catalog plugins matching ``query`` (immutable tuple)."""

        q = query or DiscoveryQuery()
        installed = {p.manifest.id: p for p in self._registry.list_installed()}
        results: list[PluginManifest] = []
        for manifest in self._registry.list_plugins():
            if (
                q.category is not None
                and manifest.category.lower() != q.category.lower()
            ):
                continue
            if q.author is not None and manifest.author.lower() != q.author.lower():
                continue
            if q.sdk_version is not None:
                want = _sdk_major(q.sdk_version)
                have = _sdk_major(manifest.sdk_version)
                if want is not None and have is not None and want != have:
                    continue
                if want is None and q.sdk_version.strip() not in manifest.sdk_version:
                    continue
            record = installed.get(manifest.id)
            is_installed = record is not None
            if q.installed is not None and is_installed != q.installed:
                continue
            if q.enabled is not None:
                if record is None or record.enabled != q.enabled:
                    continue
            results.append(manifest)
        return tuple(results)

    def installed(
        self,
        *,
        enabled: bool | None = None,
    ) -> tuple[InstalledPlugin, ...]:
        """Return install records, optionally filtered by enabled flag."""

        records = self._registry.list_installed()
        if enabled is None:
            return records
        return tuple(r for r in records if r.enabled is enabled)
