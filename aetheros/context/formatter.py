"""Rich formatter for Context Intelligence Engine panels."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.context.models import GraphContext


@dataclass(frozen=True, slots=True)
class ContextPanel:
    """Center-panel renderable for operational GraphContext."""

    context: GraphContext | None

    def __rich__(self) -> RenderableType:
        """Render intent, foreground, battery, cluster, history, confidence."""

        if self.context is None:
            return Panel(
                Text(
                    "CONTEXT idle.\n"
                    "Refresh ContextEngine after telemetry is flowing.\n"
                    "Read-only aggregation — no prediction.",
                    style="dim",
                ),
                title="Context",
                border_style="bright_blue",
            )
        ctx = self.context
        pattern = ctx.historical_pattern
        hist_label = pattern.label if pattern is not None else "—"
        hist_sim = f"{pattern.similarity:.0f}%" if pattern is not None else "—"
        body = Group(
            Text("CONTEXT", style="bold bright_blue"),
            Text(""),
            Text("Intent", style="bold"),
            Text(f"  {ctx.active_intent.name}  ({ctx.active_intent.source})"),
            Text(""),
            Text("Foreground", style="bold"),
            Text(f"  {ctx.foreground_process or '—'}"),
            Text(""),
            Text("Loads", style="bold"),
            Text(
                f"  CPU {ctx.cpu_load:.0f}%  "
                f"MEM {ctx.memory_load:.0f}%  "
                f"DISK {ctx.disk_load:.0f}%"
            ),
            Text(""),
            Text("Battery", style="bold"),
            Text(f"  {ctx.battery_state}"),
            Text(""),
            Text("Cluster", style="bold"),
            Text(f"  {ctx.cluster_health.title()}"),
            Text(""),
            Text("Simulation", style="bold"),
            Text(f"  {ctx.simulation_state}"),
            Text(""),
            Text("Historical Match", style="bold"),
            Text(f"  {hist_label}"),
            Text(""),
            Text("Similarity", style="bold"),
            Text(f"  {hist_sim}"),
            Text(""),
            Text("Confidence", style="bold"),
            Text(f"  {ctx.confidence}%"),
            Text(""),
            Text("Status  Read-only context aggregate", style="dim"),
        )
        return Panel(body, title="Context", border_style="bright_blue")
