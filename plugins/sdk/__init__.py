"""AetherOS v5.0 P1 Plugin SDK — sandboxed third-party intelligence plugins.

This package lives under ``plugins/sdk/`` and does **not** modify the
AetherOS core runtime (``aetheros.sdk`` remains the in-tree host SDK).
"""

from __future__ import annotations

from plugins.sdk.api import PluginHostAPI
from plugins.sdk.capabilities import CapabilityGrant, CapabilityRegistry
from plugins.sdk.context import (
    ContextAPI,
    ContextSnapshot,
    GraphAPI,
    GraphEdgeView,
    GraphNodeView,
    GraphSnapshot,
    graph_from_mapping,
)
from plugins.sdk.events import EventBus, PluginEvent
from plugins.sdk.inspector import PluginInspector, inspect_plugins
from plugins.sdk.loader import LoadedPlugin, PluginLoader, RejectedPlugin
from plugins.sdk.manifest import (
    PluginManifest,
    load_manifest,
    parse_manifest,
    sdk_constraint_allows,
)
from plugins.sdk.plugin import IntelligencePlugin
from plugins.sdk.sandbox import PluginSandbox, SandboxResult
from plugins.sdk.validator import PluginValidator, ValidationResult
from plugins.sdk.version import SDK_NAME, SDK_VERSION, SUPPORTED_CAPABILITIES

__all__ = [
    "SDK_NAME",
    "SDK_VERSION",
    "SUPPORTED_CAPABILITIES",
    "CapabilityGrant",
    "CapabilityRegistry",
    "ContextAPI",
    "ContextSnapshot",
    "EventBus",
    "GraphAPI",
    "GraphEdgeView",
    "GraphNodeView",
    "GraphSnapshot",
    "IntelligencePlugin",
    "LoadedPlugin",
    "PluginEvent",
    "PluginHostAPI",
    "PluginInspector",
    "PluginLoader",
    "PluginManifest",
    "PluginSandbox",
    "PluginValidator",
    "RejectedPlugin",
    "SandboxResult",
    "ValidationResult",
    "graph_from_mapping",
    "inspect_plugins",
    "load_manifest",
    "parse_manifest",
    "sdk_constraint_allows",
]
