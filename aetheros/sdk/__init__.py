"""AetherOS Kernel Intelligence SDK — plugin platform + public API client."""

from aetheros.sdk.api import (
    DashboardAPI,
    HistoryAPI,
    PluginAPI,
    SimulationAPI,
    TelemetryAPI,
)
from aetheros.sdk.client import AetherClient
from aetheros.sdk.context import ContextResource
from aetheros.sdk.graph import GraphResource
from aetheros.sdk.loader import LoadedPlugin, PluginLoader, RejectedPlugin
from aetheros.sdk.plugin import (
    AetherPlugin,
    PluginDashboardWidget,
    PluginLearningAnalyzer,
    PluginPolicyRule,
    PluginSimulationModel,
    PluginTelemetrySample,
)
from aetheros.sdk.reasoning import ReasoningResource
from aetheros.sdk.registry import PluginRecord, PluginRegistry
from aetheros.sdk.research import ResearchResource
from aetheros.sdk.sandbox import PluginSandbox, SandboxResult
from aetheros.sdk.twin import TwinResource

__all__ = [
    "AetherClient",
    "AetherPlugin",
    "ContextResource",
    "DashboardAPI",
    "GraphResource",
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
    "ReasoningResource",
    "RejectedPlugin",
    "ResearchResource",
    "SandboxResult",
    "SimulationAPI",
    "TelemetryAPI",
    "TwinResource",
]
