"""AetherOS Kernel Intelligence SDK — safe plugin platform."""

from aetheros.sdk.api import (
    DashboardAPI,
    HistoryAPI,
    PluginAPI,
    SimulationAPI,
    TelemetryAPI,
)
from aetheros.sdk.loader import LoadedPlugin, PluginLoader, RejectedPlugin
from aetheros.sdk.plugin import (
    AetherPlugin,
    PluginDashboardWidget,
    PluginLearningAnalyzer,
    PluginPolicyRule,
    PluginSimulationModel,
    PluginTelemetrySample,
)
from aetheros.sdk.registry import PluginRecord, PluginRegistry
from aetheros.sdk.sandbox import PluginSandbox, SandboxResult

__all__ = [
    "AetherPlugin",
    "DashboardAPI",
    "HistoryAPI",
    "LoadedPlugin",
    "PluginAPI",
    "PluginDashboardWidget",
    "PluginLearningAnalyzer",
    "PluginLoader",
    "PluginPolicyRule",
    "PluginRecord",
    "PluginRegistry",
    "PluginSandbox",
    "PluginSimulationModel",
    "PluginTelemetrySample",
    "RejectedPlugin",
    "SandboxResult",
    "SimulationAPI",
    "TelemetryAPI",
]
