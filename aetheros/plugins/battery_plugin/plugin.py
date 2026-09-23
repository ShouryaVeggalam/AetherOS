"""Battery Intelligence plugin — battery telemetry only (read-only)."""

from __future__ import annotations

import psutil

from aetheros.sdk import (
    AetherPlugin,
    PluginAPI,
    PluginDashboardWidget,
    PluginTelemetrySample,
)


class BatteryIntelligencePlugin(AetherPlugin):
    """Expose battery health-oriented telemetry without OS mutation."""

    name = "Battery Intelligence"
    version = "1.0.0"
    author = "AetherOS"
    description = "Provides battery health, charge cycles estimate, and runtime."
    default_enabled = True

    def register(self, api: PluginAPI) -> None:
        """Publish battery telemetry samples through TelemetryAPI."""

        for sample in self.telemetry():
            api.telemetry.contribute(sample)
        runtime = next(
            (s.value for s in self.telemetry() if s.key == "battery.runtime_minutes"),
            "n/a",
        )
        api.dashboard.add_widget(
            PluginDashboardWidget(
                title="Battery Intelligence",
                body=f"Estimated runtime: {runtime} min (read-only).",
            )
        )

    def telemetry(self) -> tuple[PluginTelemetrySample, ...]:
        """Return battery health, cycles placeholder, and estimated runtime."""

        battery = psutil.sensors_battery()
        if battery is None:
            return (
                PluginTelemetrySample("battery.health", "Battery Health", "n/a"),
                PluginTelemetrySample("battery.cycles", "Charge Cycles", "n/a"),
                PluginTelemetrySample(
                    "battery.runtime_minutes", "Estimated Runtime", "n/a", unit="min"
                ),
            )

        # Health heuristic from charge percent + AC state (no kernel access).
        health = "Good" if battery.percent >= 40 else "Low"
        if battery.percent >= 80:
            health = "Excellent"
        # Charge cycles are not exposed by psutil on most hosts — placeholder.
        cycles = "unknown"
        if battery.secsleft is not None and battery.secsleft >= 0:
            runtime: float | str = round(battery.secsleft / 60.0, 1)
        else:
            runtime = "n/a"

        return (
            PluginTelemetrySample(
                key="battery.health",
                label="Battery Health",
                value=health,
            ),
            PluginTelemetrySample(
                key="battery.cycles",
                label="Charge Cycles",
                value=cycles,
            ),
            PluginTelemetrySample(
                key="battery.percent",
                label="Charge Percent",
                value=round(float(battery.percent), 1),
                unit="%",
            ),
            PluginTelemetrySample(
                key="battery.runtime_minutes",
                label="Estimated Runtime",
                value=runtime,
                unit="min",
            ),
        )


def create_plugin() -> AetherPlugin:
    """Factory used by the plugin loader."""

    return BatteryIntelligencePlugin()


PLUGIN = BatteryIntelligencePlugin()
