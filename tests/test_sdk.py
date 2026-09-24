"""Unit tests for Phase 10 Kernel Intelligence SDK."""

from __future__ import annotations

from pathlib import Path

from aetheros.core import AetherCore
from aetheros.sdk import (
    PluginAPI,
    PluginLoader,
    PluginRegistry,
    PluginSandbox,
    TelemetryAPI,
)


def test_sandbox_rejects_subprocess(tmp_path: Path) -> None:
    """Plugins importing subprocess must be rejected."""

    plugin_dir = tmp_path / "evil_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.py").write_text(
        "import subprocess\n\nPLUGIN = None\n",
        encoding="utf-8",
    )
    result = PluginSandbox().validate_path(plugin_dir)
    assert result.safe is False
    assert any("subprocess" in item for item in result.findings)


def test_sandbox_rejects_os_system(tmp_path: Path) -> None:
    """Plugins calling os.system must be rejected."""

    plugin_dir = tmp_path / "system_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.py").write_text(
        "import os\n\ndef run():\n    os.system('echo hi')\n",
        encoding="utf-8",
    )
    result = PluginSandbox().validate_path(plugin_dir)
    assert result.safe is False


def test_sandbox_rejects_sudo_string(tmp_path: Path) -> None:
    """Plugins mentioning sudo must be rejected."""

    plugin_dir = tmp_path / "sudo_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.py").write_text(
        "MSG = 'please use sudo'\n",
        encoding="utf-8",
    )
    result = PluginSandbox().validate_path(plugin_dir)
    assert result.safe is False


def test_sandbox_allows_safe_plugin(tmp_path: Path) -> None:
    """A clean telemetry-only plugin should pass validation."""

    plugin_dir = tmp_path / "safe_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.py").write_text(
        """
from aetheros.sdk import AetherPlugin, PluginAPI, PluginTelemetrySample

class SafePlugin(AetherPlugin):
    name = "Safe"
    version = "0.0.1"
    author = "Test"
    description = "Safe demo"

    def register(self, api: PluginAPI) -> None:
        api.telemetry.contribute(
            PluginTelemetrySample("demo", "Demo", 1.0)
        )

PLUGIN = SafePlugin()
""",
        encoding="utf-8",
    )
    result = PluginSandbox().validate_path(plugin_dir)
    assert result.safe is True


def test_loader_loads_battery_plugin() -> None:
    """Bundled battery plugin should load after sandbox checks."""

    path = (
        Path(__file__).resolve().parents[1] / "aetheros" / "plugins" / "battery_plugin"
    )
    loaded = PluginLoader().load_from_directory(path)
    assert not hasattr(loaded, "reason") or getattr(loaded, "plugin", None) is not None
    from aetheros.sdk.loader import LoadedPlugin

    assert isinstance(loaded, LoadedPlugin)
    assert loaded.plugin.name == "Battery Intelligence"
    samples = loaded.plugin.telemetry()
    keys = {sample.key for sample in samples}
    assert "battery.health" in keys
    assert "battery.runtime_minutes" in keys


def test_registry_lists_bundled_plugins(tmp_path: Path) -> None:
    """Default registry should discover CPU, Battery, and GPU plugins."""

    plugins_root = Path(__file__).resolve().parents[1] / "aetheros" / "plugins"
    registry = PluginRegistry(
        plugin_dirs=(plugins_root,),
        state_path=tmp_path / "plugin_state.json",
    )
    records = registry.load_plugins()
    names = {item.name for item in records}
    assert "CPU Monitor" in names
    assert "Battery Intelligence" in names
    assert "GPU Simulator" in names
    gpu = next(item for item in records if item.name == "GPU Simulator")
    assert gpu.enabled is False
    summary = registry.safety_summary()
    assert summary["verified"] >= 3
    assert summary["unsafe"] == 0


def test_enable_disable_plugin(tmp_path: Path) -> None:
    """Registry should persist enable/disable state."""

    plugins_root = Path(__file__).resolve().parents[1] / "aetheros" / "plugins"
    registry = PluginRegistry(
        plugin_dirs=(plugins_root,),
        state_path=tmp_path / "state.json",
    )
    registry.load_plugins()
    registry.disable_plugin("CPU Monitor")
    assert registry._records["CPU Monitor"].enabled is False
    registry.enable_plugin("CPU Monitor")
    assert registry._records["CPU Monitor"].enabled is True


def test_telemetry_api_has_no_db_handle() -> None:
    """TelemetryAPI should not expose database attributes."""

    api = TelemetryAPI()
    assert not hasattr(api, "db_path")
    assert not hasattr(api, "connection")


def test_aether_core_bootstrap(tmp_path: Path) -> None:
    """AetherCore bootstrap should return a populated registry."""

    plugins_root = Path(__file__).resolve().parents[1] / "aetheros" / "plugins"
    core = AetherCore()
    core.registry = PluginRegistry(
        plugin_dirs=(plugins_root,),
        state_path=tmp_path / "core_state.json",
    )
    registry = core.bootstrap()
    assert len(registry.list_plugins()) >= 3
    assert isinstance(core.api, PluginAPI)
