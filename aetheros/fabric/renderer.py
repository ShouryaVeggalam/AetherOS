"""Fabric Rich panel — universe, federation, twin, knowledge, sync.

Presentation only.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.fabric.runtime import FabricReport


@dataclass(frozen=True, slots=True)
class FabricPanel:
    """Center-panel renderable for Aether Fabric."""

    report: FabricReport | None

    def __rich__(self) -> RenderableType:
        """Render the Fabric overview."""

        if self.report is None:
            return Panel(
                Text(
                    "Fabric idle.\n"
                    "Press F for Aether Fabric.\n"
                    "Simulation only — humans approve recommendations.",
                    style="dim",
                ),
                title="Aether Fabric",
                border_style="bright_white",
            )
        report = self.report
        census = report.census
        body = Group(
            Text("FABRIC", style="bold bright_white"),
            Text("Universal Intelligence Layer", style="dim"),
            Text(""),
            Text(f"Connected Nodes   {census.connected_nodes:,}", style="bold"),
            Text(f"Regions           {census.regions}"),
            Text(f"Datacenters       {census.datacenters}"),
            Text(f"Clusters          {census.clusters:,}"),
            Text(f"Synchronization   {census.synchronization:.2f}%"),
            Text(f"Global Health     {census.global_health:.1f}%", style="bold green"),
            Text(""),
            _federation(report),
            Text(""),
            _twin(report),
            Text(""),
            _knowledge(report),
            Text(""),
            _graph(report),
            Text(""),
            _sync(report),
            Text(""),
            Text(report.status, style="dim italic"),
            Text(""),
            Text("F/ESC leave  ·  simulation only  ·  human controlled", style="dim"),
        )
        return Panel(body, title="Aether Fabric", border_style="bright_white")


def _federation(report: FabricReport) -> Group:
    """Federation health block."""

    fed = report.federation
    return Group(
        Text("Federation Health", style="bold cyan"),
        Text(
            f"  Members {fed.member_count} · Synced {fed.synced_count} · "
            f"Mean health {fed.mean_health:.1f}%"
        ),
    )


def _twin(report: FabricReport) -> Group:
    """Digital twin highlights."""

    lines: list[Text] = [Text("Digital Twin", style="bold cyan")]
    plan = report.twin.plan
    if plan.recommended:
        rec = plan.recommended
        lines.append(
            Text(
                f"  Focus: {rec.scenario.title} — "
                f"cap {rec.capacity:.0f} / stab {rec.stability:.0f} / "
                f"lat {rec.latency:.0f} / risk {rec.risk:.0f}"
            )
        )
    for outcome in plan.outcomes[:3]:
        lines.append(Text(f"  • {outcome.scenario.title}: risk {outcome.risk:.0f}"))
    return Group(*lines)


def _knowledge(report: FabricReport) -> Table:
    """Knowledge network samples."""

    table = Table(title="Knowledge Network", expand=True, pad_edge=False)
    table.add_column("Statement")
    table.add_column("Conf", justify="right", width=6)
    if not report.knowledge:
        table.add_row("—", "—")
    for record in report.knowledge[:3]:
        table.add_row(
            record.statement[:56] + ("…" if len(record.statement) > 56 else ""),
            f"{record.confidence:.0%}",
        )
    return table


def _graph(report: FabricReport) -> Group:
    """Global graph sample edges."""

    lines: list[Text] = [
        Text("Global Graph", style="bold cyan"),
        Text(f"  Sample nodes {report.graph_nodes} · edges {report.graph_edges}"),
    ]
    for src, rel, dst in report.sample_edges[:5]:
        lines.append(Text(f"  {src} —{rel}→ {dst}"))
    return Group(*lines)


def _sync(report: FabricReport) -> Group:
    """Live synchronization notes."""

    sync = report.sync
    lines: list[Text] = [
        Text("Live Synchronization", style="bold cyan"),
        Text(
            f"  Events {sync.events_processed} · Updated {sync.nodes_updated} · "
            f"Sync {sync.synchronization:.2f}%"
        ),
    ]
    for note in sync.notes[:2]:
        lines.append(Text(f"  {note}", style="dim"))
    return Group(*lines)
