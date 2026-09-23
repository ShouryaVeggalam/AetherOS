"""CPU Monitor plugin — contributes CPU-focused telemetry and a policy tip."""

from __future__ import annotations

from aetheros.sdk import (
    AetherPlugin,
    PluginAPI,
    PluginDashboardWidget,
    PluginPolicyRule,
    PluginTelemetrySample,
)


class CPUMonitorPlugin(AetherPlugin):
    """Bundled plugin that surfaces CPU health signals."""

    name = "CPU Monitor"
    version = "1.0.0"
    author = "AetherOS"
    description = "Contributes CPU telemetry samples and a lightweight policy tip."
    default_enabled = True

    def register(self, api: PluginAPI) -> None:
        """Register CPU contributions with the safe SDK API."""

        cpu = api.telemetry.get_cpu_percent()
        api.telemetry.contribute(
            PluginTelemetrySample(
                key="cpu.plugin.load",
                label="CPU Load (plugin)",
                value=round(cpu, 1),
                unit="%",
            )
        )
        api.add_policy(
            PluginPolicyRule(
                name="cpu_headroom",
                description="Keep interactive headroom when CPU exceeds 85%.",
                severity="warning" if cpu >= 85 else "info",
            )
        )
        api.dashboard.add_widget(
            PluginDashboardWidget(
                title="CPU Monitor",
                body=f"Host CPU reported at {cpu:.0f}% via TelemetryAPI.",
            )
        )


def create_plugin() -> AetherPlugin:
    """Factory used by the plugin loader."""

    return CPUMonitorPlugin()


PLUGIN = CPUMonitorPlugin()
