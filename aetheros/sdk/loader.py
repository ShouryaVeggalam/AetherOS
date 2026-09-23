"""Dynamic plugin loader for AetherOS.

Imports plugin packages only after sandbox validation succeeds.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from aetheros.sdk.plugin import AetherPlugin
from aetheros.sdk.sandbox import PluginSandbox, SandboxResult


@dataclass(frozen=True, slots=True)
class LoadedPlugin:
    """A successfully imported plugin plus its sandbox result."""

    plugin: AetherPlugin
    module_name: str
    path: Path
    sandbox: SandboxResult


@dataclass(frozen=True, slots=True)
class RejectedPlugin:
    """A plugin path that failed sandbox or import."""

    path: Path
    reason: str
    sandbox: SandboxResult | None = None


class PluginLoader:
    """Load AetherPlugin instances from plugin directories."""

    def __init__(self, sandbox: PluginSandbox | None = None) -> None:
        """Create a loader with an optional custom sandbox."""

        self._sandbox = sandbox or PluginSandbox()

    def load_from_directory(self, plugin_dir: Path) -> LoadedPlugin | RejectedPlugin:
        """Validate and import one plugin package directory.

        Expects either:
        - plugin.py exposing `PLUGIN` (instance) or `create_plugin()`
        - __init__.py exposing the same

        Args:
            plugin_dir: Path to the plugin package folder.

        Returns:
            LoadedPlugin on success, RejectedPlugin on failure.
        """

        plugin_dir = Path(plugin_dir).resolve()
        if not plugin_dir.is_dir():
            return RejectedPlugin(path=plugin_dir, reason="Not a directory.")

        sandbox_result = self._sandbox.validate_path(plugin_dir)
        if not sandbox_result.safe:
            return RejectedPlugin(
                path=plugin_dir,
                reason=sandbox_result.reason,
                sandbox=sandbox_result,
            )

        entry = plugin_dir / "plugin.py"
        if not entry.exists():
            entry = plugin_dir / "__init__.py"
        if not entry.exists():
            return RejectedPlugin(
                path=plugin_dir,
                reason="Missing plugin.py or __init__.py entry point.",
                sandbox=sandbox_result,
            )

        module_name = f"aetheros_plugin_{plugin_dir.name}"
        try:
            module = self._import_module(module_name, entry)
            plugin = self._extract_plugin(module)
        except Exception as exc:  # noqa: BLE001 — surface load errors safely
            return RejectedPlugin(
                path=plugin_dir,
                reason=f"Import failed: {exc}",
                sandbox=sandbox_result,
            )

        if plugin is None:
            return RejectedPlugin(
                path=plugin_dir,
                reason="Entry point did not expose PLUGIN or create_plugin().",
                sandbox=sandbox_result,
            )

        return LoadedPlugin(
            plugin=plugin,
            module_name=module_name,
            path=plugin_dir,
            sandbox=sandbox_result,
        )

    def _import_module(self, module_name: str, path: Path) -> ModuleType:
        """Import a module from an explicit file path."""

        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _extract_plugin(self, module: ModuleType) -> AetherPlugin | None:
        """Pull an AetherPlugin instance from a loaded module."""

        candidate = getattr(module, "PLUGIN", None)
        if isinstance(candidate, AetherPlugin):
            return candidate
        factory = getattr(module, "create_plugin", None)
        if callable(factory):
            created = factory()
            if isinstance(created, AetherPlugin):
                return created
        # Fallback: first AetherPlugin subclass instance in module attrs.
        for value in vars(module).values():
            if isinstance(value, AetherPlugin):
                return value
        return None
