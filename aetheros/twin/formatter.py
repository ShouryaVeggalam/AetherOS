"""Rich formatter for Digital Twin 2.0 host panels.

Presentation only. Never runs scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.twin.diff import format_metric_lines
from aetheros.twin.models import SimulationScenario, TwinSnapshot
from aetheros.twin.simulator import DigitalTwinReport


@dataclass(frozen=True, slots=True)
class DigitalTwinPanel:
    """Center-panel renderable for host Digital Twin results."""

    report: DigitalTwinReport | None
    scenario: SimulationScenario | None = None
    baseline: TwinSnapshot | None = None

    def __rich__(self) -> RenderableType:
        """Render scenario, current vs simulated metrics, stability, risk."""

        if self.report is None:
            name = self.scenario.name if self.scenario is not None else "—"
            cpu = (
                f"{self.baseline.telemetry.cpu_percent:.0f}%"
                if self.baseline is not None
                else "—"
            )
            return Panel(
                Text(
                    "DIGITAL TWIN idle.\n"
                    f"Scenario queued: {name}\n"
                    f"Current CPU: {cpu}\n"
                    "Press V after telemetry is flowing.\n"
                    "D remains Developer Console — V opens the host twin.\n"
                    "Status: Simulation Only",
                    style="dim",
                ),
                title="Digital Twin",
                border_style="bright_magenta",
            )
        report = self.report
        result = report.result
        base = report.baseline.telemetry
        lines = format_metric_lines(report.diff)
        diff_block = (
            "\n".join(f"  {line}" for line in lines) if lines else "  (no metric drift)"
        )
        body = Group(
            Text("DIGITAL TWIN", style="bold bright_magenta"),
            Text(""),
            Text("Scenario", style="bold"),
            Text(f"  {result.scenario.name}"),
            Text(f"  {result.scenario.description}", style="dim"),
            Text(""),
            Text("Current", style="bold"),
            Text(
                f"  CPU {base.cpu_percent:.0f}%  "
                f"MEM {base.memory_percent:.0f}%  "
                f"DISK {base.disk_percent:.0f}%"
            ),
            Text(""),
            Text("Simulated", style="bold"),
            Text(
                f"  CPU {result.predicted_cpu:.0f}%  "
                f"MEM {result.predicted_memory:.0f}%  "
                f"DISK {result.predicted_disk:.0f}%"
            ),
            Text(""),
            Text("Diff", style="bold"),
            Text(diff_block),
            Text(""),
            Text("Stability", style="bold"),
            Text(f"  {result.stability:.0f}/100"),
            Text(""),
            Text("Risk", style="bold"),
            Text(f"  {result.risk.title()}  (bottleneck: {result.bottleneck})"),
            Text(""),
            Text("Reason", style="bold"),
            Text(f"  {result.reasoning}"),
            Text(""),
            Text("Confidence", style="bold"),
            Text(f"  {result.confidence:.0f}%"),
            Text(""),
            Text("Status  Simulation Only", style="dim"),
            Text("V/ESC leave  ·  ] cycle scenario  ·  immutable clones", style="dim"),
        )
        return Panel(body, title="Digital Twin", border_style="bright_magenta")
