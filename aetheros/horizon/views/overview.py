"""Horizon Overview — unified global infrastructure health at a glance.

Consumes ``HorizonSnapshot`` only. Never starts collectors or engines.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.horizon.snapshot import HorizonSnapshot
from aetheros.horizon.widgets.metric_grid import MetricGrid
from aetheros.horizon.widgets.stat_card import StatCard
from aetheros.horizon.widgets.timeline import Timeline


def render_overview(snapshot: HorizonSnapshot) -> RenderableType:
    """Render the Overview page from an immutable snapshot."""

    cards = MetricGrid(
        cards=(
            StatCard(
                "Global Health", f"{snapshot.global_health:.0f}", tone="bright_green"
            ),
            StatCard(
                "Providers",
                str(snapshot.connected_providers),
                tone="bright_cyan",
            ),
            StatCard("Regions", str(snapshot.regions), tone="bright_white"),
            StatCard("Clusters", str(snapshot.clusters), tone="bright_white"),
            StatCard("Nodes", str(snapshot.nodes), tone="bright_white"),
            StatCard("Discoveries", str(snapshot.discoveries), tone="bright_magenta"),
            StatCard(
                "Simulations",
                str(snapshot.active_simulations),
                tone="bright_yellow",
            ),
            StatCard(
                "Consensus",
                f"{snapshot.consensus_confidence:.0f}%",
                tone="bright_cyan",
            ),
        )
    )
    body = Group(
        Text("HORIZON OVERVIEW", style="bold bright_white"),
        Text("Read-only global infrastructure observatory", style="dim"),
        Text(""),
        cards,
        Text(""),
        Text("Recent Activity", style="bold"),
        Text(""),
        Timeline(events=snapshot.timeline_events),
    )
    return Panel(body, title="Horizon · Overview", border_style="bright_white")
