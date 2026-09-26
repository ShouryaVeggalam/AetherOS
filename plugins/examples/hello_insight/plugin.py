"""Hello Insight — example sandboxed plugin for the v5 Plugin SDK."""

from __future__ import annotations

from plugins.sdk import IntelligencePlugin, PluginHostAPI


class HelloInsightPlugin(IntelligencePlugin):
    """Registers a note and listens for telemetry ticks (read-only)."""

    id = "hello-insight"
    name = "Hello Insight"
    version = "0.1.0"
    author = "AetherOS Examples"
    description = "Example sandboxed insight plugin."

    def register(self, api: PluginHostAPI) -> None:
        api.contribute_note("Hello Insight registered (simulation / advisory only).")
        # Demonstrate read-only graph access when granted.
        graph = api.read_graph()
        api.set_meta("graph_nodes", len(graph.list_nodes()))
        ctx = api.read_context()
        api.set_meta("intent", ctx.intent() or "unset")

    def on_event(self, event: object) -> None:
        # Advisory only — never executes actions.
        return None


def create_plugin() -> IntelligencePlugin:
    return HelloInsightPlugin()


PLUGIN = HelloInsightPlugin()
