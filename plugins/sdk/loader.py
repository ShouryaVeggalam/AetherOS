"""Plugin loader — validate, sandbox, import, and register plugins.

Does not modify AetherOS core runtime. Hosts call ``load_plugin`` explicitly.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from plugins.sdk.api import PluginHostAPI
from plugins.sdk.manifest import PluginManifest
from plugins.sdk.plugin import IntelligencePlugin
from plugins.sdk.sandbox import PluginSandbox, SandboxResult
from plugins.sdk.validator import PluginValidator, ValidationResult


@dataclass(frozen=True, slots=True)
class LoadedPlugin:
    """Successfully loaded plugin session."""

    plugin: IntelligencePlugin
    manifest: PluginManifest
    path: Path
    module_name: str
    sandbox: SandboxResult
    api: PluginHostAPI


@dataclass(frozen=True, slots=True)
class RejectedPlugin:
    """Plugin package that failed validation, sandbox, or import."""

    path: Path
    reason: str
    validation: ValidationResult | None = None
    sandbox: SandboxResult | None = None


class PluginLoader:
    """Load IntelligencePlugin packages from directories."""

    def __init__(
        self,
        *,
        validator: PluginValidator | None = None,
        sandbox: PluginSandbox | None = None,
    ) -> None:
        self._validator = validator or PluginValidator()
        self._sandbox = sandbox or PluginSandbox()

    def load_plugin(
        self,
        plugin_dir: Path | str,
        *,
        api: PluginHostAPI | None = None,
    ) -> LoadedPlugin | RejectedPlugin:
        """Validate → sandbox → import → register one plugin directory."""

        root = Path(plugin_dir).resolve()
        validation = self._validator.validate_directory(root)
        if not validation.ok or validation.manifest is None:
            return RejectedPlugin(
                path=root,
                reason=validation.reason,
                validation=validation,
            )

        sandbox_result = self._sandbox.validate_path(root)
        if not sandbox_result.safe:
            return RejectedPlugin(
                path=root,
                reason=sandbox_result.reason,
                validation=validation,
                sandbox=sandbox_result,
            )

        entry = root / validation.manifest.entry
        if not entry.exists():
            entry = root / "plugin.py"
        if not entry.exists():
            return RejectedPlugin(
                path=root,
                reason="Missing plugin entry module.",
                validation=validation,
                sandbox=sandbox_result,
            )

        module_name = f"aetheros_v5_plugin_{root.name}"
        try:
            module = self._import_module(module_name, entry)
            plugin = self._extract_plugin(module)
        except Exception as exc:  # noqa: BLE001 — surface load errors safely
            return RejectedPlugin(
                path=root,
                reason=f"Import failed: {exc}",
                validation=validation,
                sandbox=sandbox_result,
            )

        if plugin is None:
            return RejectedPlugin(
                path=root,
                reason="Entry did not expose PLUGIN or create_plugin().",
                validation=validation,
                sandbox=sandbox_result,
            )

        host_api = api or PluginHostAPI()
        # Grant declared capabilities before register().
        for cap in validation.manifest.capabilities:
            try:
                host_api.capabilities.register(cap)
            except ValueError:
                return RejectedPlugin(
                    path=root,
                    reason=f"Cannot grant capability '{cap}'.",
                    validation=validation,
                    sandbox=sandbox_result,
                )

        # Auto-subscribe declared event topics to plugin.on_event when present.
        if validation.manifest.events and host_api.capabilities.has("events.subscribe"):
            for topic in validation.manifest.events:
                host_api.events.subscribe(topic, plugin.on_event)

        try:
            plugin.register(host_api)
        except Exception as exc:  # noqa: BLE001
            return RejectedPlugin(
                path=root,
                reason=f"register() failed: {exc}",
                validation=validation,
                sandbox=sandbox_result,
            )

        return LoadedPlugin(
            plugin=plugin,
            manifest=validation.manifest,
            path=root,
            module_name=module_name,
            sandbox=sandbox_result,
            api=host_api,
        )

    def discover(self, plugins_root: Path | str) -> tuple[Path, ...]:
        """Return child directories that look like plugin packages."""

        root = Path(plugins_root)
        if not root.is_dir():
            return ()
        found: list[Path] = []
        for child in sorted(root.iterdir()):
            if not child.is_dir() or child.name.startswith("."):
                continue
            if (child / "plugin.yaml").exists() or (child / "plugin.py").exists():
                found.append(child)
        return tuple(found)

    def _import_module(self, module_name: str, path: Path) -> ModuleType:
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create module spec for {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _extract_plugin(self, module: ModuleType) -> IntelligencePlugin | None:
        candidate = getattr(module, "PLUGIN", None)
        if isinstance(candidate, IntelligencePlugin):
            return candidate
        factory = getattr(module, "create_plugin", None)
        if callable(factory):
            created = factory()
            if isinstance(created, IntelligencePlugin):
                return created
        for value in vars(module).values():
            if isinstance(value, IntelligencePlugin):
                return value
        return None
