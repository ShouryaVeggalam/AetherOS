"""Infinity Rich panel — platform identity, pipeline, generations, layers."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.infinity.runtime import InfinityReport


@dataclass(frozen=True, slots=True)
class InfinityPanel:
    """Center-panel renderable for AetherOS Infinity."""

    report: InfinityReport | None

    def __rich__(self) -> RenderableType:
        """Render the Infinity overview."""

        if self.report is None:
            return Panel(
                Text(
                    "Infinity idle.\n"
                    "Press I for AetherOS ∞.\n"
                    "Explainable Operating Intelligence — human-in-the-loop.",
                    style="dim",
                ),
                title="AetherOS ∞",
                border_style="bright_cyan",
            )
        report = self.report
        body = Group(
            Text("AETHEROS ∞", style="bold bright_cyan"),
            Text("Infinity — Explainable Operating Intelligence", style="dim"),
            Text(""),
            Text(report.identity, style="italic"),
            Text(""),
            Text(f"Generations   {report.generation_count}", style="bold"),
            Text(f"Layers ready  {report.layers_ready}/{len(report.layers)}"),
            Text(""),
            _principles(report),
            Text(""),
            _pipeline(report),
            Text(""),
            _generations(report),
            Text(""),
            _layers(report),
            Text(""),
            Text(report.status, style="dim italic"),
            Text(""),
            Text("I/ESC leave  ·  never executes  ·  humans approve", style="dim"),
        )
        return Panel(body, title="AetherOS ∞", border_style="bright_cyan")


def _principles(report: InfinityReport) -> Group:
    """Core principles list."""

    lines: list[Text] = [Text("Principles", style="bold cyan")]
    for principle in report.principles:
        lines.append(Text(f"  • {principle}"))
    return Group(*lines)


def _pipeline(report: InfinityReport) -> Group:
    """Intelligence pipeline stages."""

    lines: list[Text] = [Text("Intelligence Pipeline", style="bold cyan")]
    names = " → ".join(stage.name for stage in report.pipeline)
    lines.append(Text(f"  {names}"))
    return Group(*lines)


def _generations(report: InfinityReport) -> Table:
    """Generation catalog table."""

    table = Table(title="Major Generations", expand=True, pad_edge=False)
    table.add_column("Ver", width=4)
    table.add_column("Codename", width=22)
    table.add_column("Summary")
    for gen in report.generations:
        table.add_row(gen.version, gen.codename, gen.summary[:48])
    return table


def _layers(report: InfinityReport) -> Table:
    """Live layer status."""

    table = Table(title="Layer Status", expand=True, pad_edge=False)
    table.add_column("Layer")
    table.add_column("Ready", width=6)
    table.add_column("Detail")
    for layer in report.layers:
        table.add_row(layer.name, "yes" if layer.ready else "no", layer.detail)
    return table
