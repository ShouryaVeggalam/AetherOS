"""Safe SDK APIs exposed to plugins.

Plugins receive these facades only — never raw database handles,
filesystem roots, or process control primitives.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from aetheros.sdk.plugin import (
    PluginDashboardWidget,
    PluginLearningAnalyzer,
    PluginPolicyRule,
    PluginSimulationModel,
    PluginTelemetrySample,
)


@dataclass
class TelemetryAPI:
    """Read-only telemetry facade for plugins."""

    _snapshot: dict[str, Any] = field(default_factory=dict)
    _contributions: list[PluginTelemetrySample] = field(default_factory=list)

    def set_host_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Publish a sanitized host snapshot for plugin consumers."""

        self._snapshot = dict(snapshot)

    def get_cpu_percent(self) -> float:
        """Return the latest host CPU percent, or 0.0 if unknown."""

        return float(self._snapshot.get("cpu_percent", 0.0))

    def get_memory_percent(self) -> float:
        """Return the latest host memory percent, or 0.0 if unknown."""

        return float(self._snapshot.get("memory_percent", 0.0))

    def get_battery_percent(self) -> float | None:
        """Return battery percent when present."""

        value = self._snapshot.get("battery_percent")
        return float(value) if value is not None else None

    def contribute(self, sample: PluginTelemetrySample) -> None:
        """Register a telemetry sample from a plugin."""

        self._contributions.append(sample)

    def contributions(self) -> tuple[PluginTelemetrySample, ...]:
        """Return all plugin-contributed telemetry samples."""

        return tuple(self._contributions)


@dataclass
class DashboardAPI:
    """Dashboard contribution facade for plugins."""

    _widgets: list[PluginDashboardWidget] = field(default_factory=list)

    def add_widget(self, widget: PluginDashboardWidget) -> None:
        """Register a dashboard widget descriptor."""

        self._widgets.append(widget)

    def widgets(self) -> tuple[PluginDashboardWidget, ...]:
        """Return registered dashboard widgets."""

        return tuple(self._widgets)


@dataclass
class HistoryAPI:
    """Read-only history facade (no direct database access)."""

    _entries: list[dict[str, Any]] = field(default_factory=list)

    def set_entries(self, entries: list[dict[str, Any]]) -> None:
        """Provide sanitized history rows to plugins."""

        self._entries = [dict(item) for item in entries]

    def recent(self, limit: int = 5) -> tuple[dict[str, Any], ...]:
        """Return the most recent sanitized history entries."""

        return tuple(self._entries[: max(0, limit)])

    def count(self) -> int:
        """Return how many history entries are visible to plugins."""

        return len(self._entries)


@dataclass
class SimulationAPI:
    """Safe simulation facade — what-if only, never OS mutation."""

    _models: list[PluginSimulationModel] = field(default_factory=list)

    def register_model(self, model: PluginSimulationModel) -> None:
        """Register a plugin simulation model descriptor."""

        self._models.append(model)

    def models(self) -> tuple[PluginSimulationModel, ...]:
        """Return registered simulation models."""

        return tuple(self._models)

    def estimate_improvement(self, cpu_delta: float, memory_delta: float) -> float:
        """Return a crude 0–100 improvement estimate from deltas."""

        relief = max(0.0, -cpu_delta) + max(0.0, -memory_delta) * 0.5
        return float(max(0.0, min(100.0, 50.0 + relief)))


@dataclass
class PluginAPI:
    """Aggregate safe API surface handed to plugins at register() time."""

    telemetry: TelemetryAPI = field(default_factory=TelemetryAPI)
    dashboard: DashboardAPI = field(default_factory=DashboardAPI)
    history: HistoryAPI = field(default_factory=HistoryAPI)
    simulation: SimulationAPI = field(default_factory=SimulationAPI)
    policy_rules: list[PluginPolicyRule] = field(default_factory=list)
    learning_analyzers: list[PluginLearningAnalyzer] = field(default_factory=list)

    def add_policy(self, rule: PluginPolicyRule) -> None:
        """Register a policy rule contribution."""

        self.policy_rules.append(rule)

    def add_learning(self, analyzer: PluginLearningAnalyzer) -> None:
        """Register a learning analyzer contribution."""

        self.learning_analyzers.append(analyzer)

    def stamp(self) -> str:
        """Return a UTC timestamp string for plugin logging (text only)."""

        return datetime.now(timezone.utc).isoformat()
