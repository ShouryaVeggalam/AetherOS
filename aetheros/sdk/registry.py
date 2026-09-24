"""Plugin registry — discover, load, enable, and disable plugins."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from aetheros.sdk.api import PluginAPI
from aetheros.sdk.loader import PluginLoader, RejectedPlugin
from aetheros.sdk.plugin import AetherPlugin
from aetheros.sdk.sandbox import SandboxResult


@dataclass
class PluginRecord:
    """Registry metadata for one discovered plugin."""

    name: str
    version: str
    author: str
    description: str
    path: Path
    enabled: bool
    verified: bool
    safety_reason: str
    plugin: AetherPlugin | None = None
    findings: tuple[str, ...] = ()


@dataclass
class PluginRegistry:
    """Discover plugins under configured directories and manage lifecycle.

    Args:
        plugin_dirs: Directories to scan for plugin packages.
        state_path: JSON file storing enabled/disabled flags.
        loader: Plugin loader used for sandbox + import.
        api: Shared safe PluginAPI facade.
    """

    plugin_dirs: tuple[Path, ...] = field(default_factory=tuple)
    state_path: Path = field(default_factory=lambda: Path("data/plugin_state.json"))
    loader: PluginLoader = field(default_factory=PluginLoader)
    api: PluginAPI = field(default_factory=PluginAPI)
    _records: dict[str, PluginRecord] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Normalize paths after initialization."""

        self.plugin_dirs = tuple(Path(p) for p in self.plugin_dirs)
        self.state_path = Path(self.state_path)

    @classmethod
    def default(cls) -> PluginRegistry:
        """Create a registry pointed at the bundled plugins package."""

        package_plugins = Path(__file__).resolve().parent.parent / "plugins"
        cwd_plugins = Path("plugins")
        dirs = [package_plugins]
        if cwd_plugins.exists() and cwd_plugins.resolve() != package_plugins:
            dirs.append(cwd_plugins)
        return cls(plugin_dirs=tuple(dirs))

    def discover_plugins(self) -> list[Path]:
        """Return candidate plugin directories (folders with plugin.py)."""

        found: list[Path] = []
        for root in self.plugin_dirs:
            if not root.is_dir():
                continue
            for child in sorted(root.iterdir()):
                if not child.is_dir() or child.name.startswith("_"):
                    continue
                if (child / "plugin.py").exists() or (child / "__init__.py").exists():
                    found.append(child)
        return found

    def load_plugins(self) -> list[PluginRecord]:
        """Discover, sandbox, import, and register all plugins.

        Returns:
            The list of PluginRecord entries after loading.
        """

        state = self._load_state()
        self._records.clear()
        # Reset contribution lists on the shared API.
        self.api = PluginAPI()

        for path in self.discover_plugins():
            result = self.loader.load_from_directory(path)
            if isinstance(result, RejectedPlugin):
                name = path.name
                sandbox = result.sandbox or SandboxResult(
                    safe=False, reason=result.reason, findings=()
                )
                self._records[name] = PluginRecord(
                    name=name,
                    version="unknown",
                    author="unknown",
                    description=result.reason,
                    path=path,
                    enabled=False,
                    verified=False,
                    safety_reason=result.reason,
                    plugin=None,
                    findings=sandbox.findings,
                )
                continue

            plugin = result.plugin
            enabled = (
                state[plugin.name]
                if plugin.name in state
                else bool(getattr(plugin, "default_enabled", True))
            )
            record = PluginRecord(
                name=plugin.name,
                version=plugin.version,
                author=plugin.author,
                description=plugin.description,
                path=result.path,
                enabled=enabled,
                verified=True,
                safety_reason=result.sandbox.reason,
                plugin=plugin,
                findings=(),
            )
            self._records[plugin.name] = record
            if enabled:
                self._activate(plugin)

        self._save_state()
        return self.list_plugins()

    def list_plugins(self) -> list[PluginRecord]:
        """Return all known plugin records sorted by name."""

        return sorted(self._records.values(), key=lambda item: item.name.lower())

    def enable_plugin(self, name: str) -> PluginRecord:
        """Enable a verified plugin and call register()."""

        record = self._require(name)
        if not record.verified or record.plugin is None:
            raise ValueError(f"Cannot enable unsafe/unloaded plugin '{name}'.")
        if not record.enabled:
            record.enabled = True
            self._activate(record.plugin)
            self._save_state()
        return record

    def disable_plugin(self, name: str) -> PluginRecord:
        """Disable a plugin (contributions cleared on next load_plugins)."""

        record = self._require(name)
        record.enabled = False
        self._save_state()
        # Rebuild API from remaining enabled plugins.
        self.api = PluginAPI()
        for item in self._records.values():
            if item.enabled and item.plugin is not None:
                self._activate(item.plugin)
        return record

    def safety_summary(self) -> dict[str, int]:
        """Return counts of verified vs unsafe plugins."""

        verified = sum(1 for item in self._records.values() if item.verified)
        unsafe = sum(1 for item in self._records.values() if not item.verified)
        return {"verified": verified, "unsafe": unsafe}

    def _activate(self, plugin: AetherPlugin) -> None:
        """Register a plugin and merge its default contributions into the API."""

        plugin.register(self.api)
        for sample in plugin.telemetry():
            self.api.telemetry.contribute(sample)
        for rule in plugin.policies():
            self.api.add_policy(rule)
        for widget in plugin.dashboard():
            self.api.dashboard.add_widget(widget)
        for analyzer in plugin.learning():
            self.api.add_learning(analyzer)
        for model in plugin.simulation():
            self.api.simulation.register_model(model)

    def _require(self, name: str) -> PluginRecord:
        """Fetch a record or raise KeyError."""

        if name not in self._records:
            raise KeyError(f"Unknown plugin '{name}'.")
        return self._records[name]

    def _load_state(self) -> dict[str, bool]:
        """Load enabled flags from JSON."""

        if not self.state_path.exists():
            return {}
        try:
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(key): bool(value) for key, value in data.items()}

    def _save_state(self) -> None:
        """Persist enabled flags to JSON."""

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {name: record.enabled for name, record in self._records.items()}
        self.state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
