"""Core facade that wires the SDK into the AetherOS runtime."""

from __future__ import annotations

from dataclasses import dataclass, field

from aetheros.sdk import PluginAPI, PluginRegistry


@dataclass
class AetherCore:
    """Lightweight core hosting the plugin registry and shared API.

    Args:
        registry: Plugin registry (defaults to bundled plugins/).
    """

    registry: PluginRegistry = field(default_factory=PluginRegistry.default)

    def bootstrap(self) -> PluginRegistry:
        """Discover and load plugins, returning the populated registry."""

        self.registry.load_plugins()
        return self.registry

    @property
    def api(self) -> PluginAPI:
        """Return the shared safe plugin API facade."""

        return self.registry.api
