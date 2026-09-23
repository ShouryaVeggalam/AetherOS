"""GPU Simulator example plugin — simulation model contribution (disabled by default)."""

from __future__ import annotations

from aetheros.sdk import (
    AetherPlugin,
    PluginAPI,
    PluginDashboardWidget,
    PluginSimulationModel,
)


class GPUSimulatorPlugin(AetherPlugin):
    """Example plugin registering a placeholder GPU simulation model."""

    name = "GPU Simulator"
    version = "0.1.0"
    author = "AetherOS Examples"
    description = "Example simulation-model plugin (disabled by default)."
    default_enabled = False

    def register(self, api: PluginAPI) -> None:
        """Register the example GPU simulation model."""

        for model in self.simulation():
            api.simulation.register_model(model)
        api.dashboard.add_widget(
            PluginDashboardWidget(
                title="GPU Simulator",
                body="Placeholder GPU model — simulation only, never executes.",
            )
        )

    def simulation(self):
        """Return the example simulation model descriptor."""

        return (
            PluginSimulationModel(
                name="gpu_placeholder",
                description="Hypothetical GPU throughput model for research demos.",
            ),
        )


def create_plugin() -> AetherPlugin:
    """Factory used by the plugin loader."""

    return GPUSimulatorPlugin()


PLUGIN = GPUSimulatorPlugin()
