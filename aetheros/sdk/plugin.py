"""Base plugin interface for the AetherOS Kernel Intelligence SDK.

Plugins contribute read-only capabilities. They must never execute shell
commands, use sudo, or modify kernel state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PluginTelemetrySample:
    """One telemetry contribution from a plugin (read-only)."""

    key: str
    label: str
    value: float | str | None
    unit: str = ""


@dataclass(frozen=True, slots=True)
class PluginPolicyRule:
    """A policy tip contributed by a plugin (advice text only)."""

    name: str
    description: str
    severity: str = "info"


@dataclass(frozen=True, slots=True)
class PluginDashboardWidget:
    """Descriptor for a dashboard contribution."""

    title: str
    body: str


@dataclass(frozen=True, slots=True)
class PluginLearningAnalyzer:
    """Descriptor for a learning/analysis contribution."""

    name: str
    summary: str


@dataclass(frozen=True, slots=True)
class PluginSimulationModel:
    """Descriptor for a simulation model contribution."""

    name: str
    description: str


class AetherPlugin(ABC):
    """Abstract base class every AetherOS plugin must implement.

    Attributes:
        name: Human-readable plugin name.
        version: Semantic version string.
        author: Plugin author or organization.
        description: Short summary of what the plugin provides.
    """

    name: str
    version: str
    author: str
    description: str
    default_enabled: bool = True

    @abstractmethod
    def register(self, api: Any) -> None:
        """Register this plugin with the safe SDK API facade.

        Args:
            api: A PluginAPI instance exposing only safe interfaces.
        """

    def telemetry(self) -> Sequence[PluginTelemetrySample]:
        """Return optional telemetry samples contributed by this plugin."""

        return ()

    def policies(self) -> Sequence[PluginPolicyRule]:
        """Return optional policy rules contributed by this plugin."""

        return ()

    def dashboard(self) -> Sequence[PluginDashboardWidget]:
        """Return optional dashboard widgets contributed by this plugin."""

        return ()

    def learning(self) -> Sequence[PluginLearningAnalyzer]:
        """Return optional learning analyzers contributed by this plugin."""

        return ()

    def simulation(self) -> Sequence[PluginSimulationModel]:
        """Return optional simulation models contributed by this plugin."""

        return ()
