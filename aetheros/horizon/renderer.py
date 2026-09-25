"""Horizon Rich panel — planetary intelligence overview.

Presentation only. No simulation logic here.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.horizon.runtime import HorizonReport


@dataclass(frozen=True, slots=True)
class HorizonPanel:
    """Center-panel renderable for Horizon planetary intelligence."""

    report: HorizonReport | None
    view: str = "world"

    def __rich__(self) -> RenderableType:
        """Render the Horizon overview."""

        if self.report is None:
            return Panel(
                Text(
                    "Horizon idle.\n"
                    "Press H for Planetary Intelligence Network.\n"
                    "Simulation-first — humans approve actions.",
                    style="dim",
                ),
                title="Horizon",
                border_style="bright_blue",
            )
        report = self.report
        census = report.world.census
        body = Group(
            Text("HORIZON", style="bold bright_blue"),
            Text("Planetary Intelligence Network", style="dim"),
            Text(""),
            Text(f"World Health  {census.world_health:.1f}%", style="bold green"),
            Text(""),
            _census_table(report),
            Text(""),
            _simulation_block(report),
            Text(""),
            _latency_block(report),
            Text(""),
            _capacity_block(report),
            Text(""),
            Text(report.status, style="dim italic"),
            Text(""),
            Text("H/ESC leave  ·  ? help  ·  simulation only", style="dim"),
        )
        return Panel(body, title="Horizon", border_style="bright_blue")


def _census_table(report: HorizonReport) -> Table:
    """World census summary."""

    c = report.world.census
    table = Table(title="World Map Census", expand=True, pad_edge=False)
    table.add_column("Layer")
    table.add_column("Count", justify="right")
    for label, value in (
        ("Regions", f"{c.regions:,}"),
        ("Datacenters", f"{c.datacenters:,}"),
        ("Clusters", f"{c.clusters:,}"),
        ("Nodes", f"{c.nodes:,}"),
        ("Edge devices", f"{c.edge_devices:,}"),
        ("Robots", f"{c.robots:,}"),
        ("Satellites", f"{c.satellites:,}"),
        ("HPC clusters", f"{c.hpc_clusters:,}"),
    ):
        table.add_row(label, value)
    return table


def _simulation_block(report: HorizonReport) -> Group:
    """Active resilience simulation summary."""

    r = report.resilience
    return Group(
        Text("Simulation", style="bold cyan"),
        Text(f"  {r.scenario.description}"),
        Text(f"  Remaining capacity  {r.remaining_capacity_pct:.1f}%"),
        Text(f"  Cluster health      {r.cluster_health:.1f}%"),
        Text(f"  Global stability    {r.global_stability:.1f}%"),
        Text(
            f"  Global Health       {r.world_health_after:.1f}%",
            style="bold yellow",
        ),
    )


def _latency_block(report: HorizonReport) -> Group:
    """Top latency estimates."""

    lines: list[Text] = [Text("Latency Graph", style="bold cyan")]
    if not report.latency:
        lines.append(Text("  No region pairs.", style="dim"))
        return Group(*lines)
    for est in report.latency[:5]:
        lines.append(
            Text(
                f"  {est.source_id} → {est.target_id}: "
                f"{est.estimated_ms:.1f} ms "
                f"(conf {est.confidence:.0%}, rel {est.reliability:.0%})"
            )
        )
    return Group(*lines)


def _capacity_block(report: HorizonReport) -> Group:
    """Capacity forecast highlights (24h)."""

    lines: list[Text] = [Text("Capacity (24h)", style="bold cyan")]
    day = [f for f in report.capacity.forecasts if f.horizon == "24h"]
    for forecast in day:
        lines.append(
            Text(
                f"  {forecast.resource}: {forecast.baseline:.1f} → "
                f"{forecast.projected:.1f} ({forecast.growth_pct:+.2f}%)"
            )
        )
    return Group(*lines)
