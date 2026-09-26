"""Atlas Overview — unified infrastructure health at a glance.

Consumes ``AtlasSnapshot`` only. Never starts collectors or engines.
"""

from __future__ import annotations

from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.atlas.snapshot import AtlasSnapshot
from aetheros.atlas.widgets.progress_bar import AtlasProgressBar
from aetheros.atlas.widgets.stat_card import StatCard


def render_overview(snapshot: AtlasSnapshot) -> RenderableType:
    """Render the Overview page from an immutable snapshot."""

    cards = Columns(
        [
            StatCard(
                "Connected Nodes",
                str(snapshot.connected_nodes),
                tone="bright_cyan",
            ),
            StatCard(
                "Online %",
                f"{snapshot.online_percent():.0f}%",
                tone="bright_green",
            ),
            StatCard(
                "Cluster Health",
                f"{snapshot.cluster_health:.0f}",
                tone="bright_white",
            ),
            StatCard(
                "Discoveries",
                str(snapshot.discoveries),
                tone="bright_magenta",
            ),
            StatCard(
                "Simulations",
                str(snapshot.active_simulations),
                tone="bright_yellow",
            ),
            StatCard(
                "Consensus",
                _consensus_label(snapshot),
                tone="bright_white",
            ),
        ],
        equal=True,
        expand=True,
    )
    resources = Group(
        Text("Resources", style="bold"),
        Text(""),
        AtlasProgressBar("CPU", snapshot.cpu_percent),
        AtlasProgressBar("Memory", snapshot.memory_percent),
        AtlasProgressBar("Disk", snapshot.disk_percent),
    )
    body = Group(
        Text("ATLAS OVERVIEW", style="bold bright_white"),
        Text("Read-only distributed observatory", style="dim"),
        Text(""),
        cards,
        Text(""),
        Panel(resources, border_style="grey37", padding=(0, 1)),
    )
    return Panel(body, title="Atlas · Overview", border_style="bright_white")


def _consensus_label(snapshot: AtlasSnapshot) -> str:
    decision = snapshot.consensus_decision
    if decision is None:
        return "—"
    conf = getattr(decision, "confidence", None)
    if conf is None:
        return "ready"
    return f"{float(conf):.0f}%"
