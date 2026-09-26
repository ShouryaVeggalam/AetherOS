"""Horizon Health — unified green / yellow / red subsystem diagnostics.

Presentation indicators only. Never runs health probes itself.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.horizon.snapshot import HealthSignal, HorizonSnapshot
from aetheros.horizon.widgets.table import HorizonTable

_DEFAULT_NAMES = (
    "Federation",
    "Graph",
    "Scheduler",
    "Twin",
    "Knowledge",
    "Research",
    "Consensus",
)

_STATUS_STYLE = {
    "green": "bright_green",
    "yellow": "bright_yellow",
    "red": "bright_red",
}


def render_health(snapshot: HorizonSnapshot) -> RenderableType:
    """Render unified health board from snapshot signals."""

    signals = snapshot.health_signals or _derive_signals(snapshot)
    rows = tuple(
        (
            signal.name,
            "●",
            signal.status.upper(),
            signal.detail or "—",
        )
        for signal in signals
    )
    # Colorize via Text rows by rebuilding as Group for status column clarity.
    table = HorizonTable(
        columns=("Subsystem", "", "Status", "Detail"),
        rows=rows,
    )
    legend = Text.assemble(
        ("Legend  ", "dim"),
        ("●", "bright_green"),
        (" green  ", "dim"),
        ("●", "bright_yellow"),
        (" yellow  ", "dim"),
        ("●", "bright_red"),
        (" red", "dim"),
    )
    body = Group(
        Text("HEALTH", style="bold bright_white"),
        Text("Unified diagnostics · green / yellow / red only", style="dim"),
        Text(""),
        table,
        Text(""),
        legend,
        Text(""),
        *(_signal_lines(signals)),
    )
    return Panel(body, title="Horizon · Health", border_style="bright_white")


def _signal_lines(signals: tuple[HealthSignal, ...]) -> list[Text]:
    lines: list[Text] = []
    for signal in signals:
        style = _STATUS_STYLE.get(signal.status, "white")
        lines.append(
            Text.assemble(
                (f"  {signal.name:<12} ", ""),
                ("● ", style),
                (signal.status.upper(), style),
                (f"  {signal.detail}" if signal.detail else "", "dim"),
            )
        )
    return lines


def _derive_signals(snapshot: HorizonSnapshot) -> tuple[HealthSignal, ...]:
    """Best-effort signals from snapshot presence (presentation only)."""

    federation = (
        HealthSignal("Federation", "green", f"{snapshot.connected_providers} providers")
        if snapshot.connected_providers > 0 or snapshot.cloud_snapshot is not None
        else HealthSignal("Federation", "yellow", "no providers")
    )
    graph = (
        HealthSignal("Graph", "green", "topology present")
        if snapshot.topology_graph is not None
        else HealthSignal("Graph", "yellow", "no topology")
    )
    scheduler = (
        HealthSignal("Scheduler", "green", "plan ready")
        if snapshot.schedule_decision is not None
        else HealthSignal("Scheduler", "yellow", "idle")
    )
    twin = (
        HealthSignal("Twin", "green", snapshot.twin_scenario_name or "ready")
        if snapshot.twin_run is not None
        else HealthSignal("Twin", "yellow", "idle")
    )
    knowledge = (
        HealthSignal("Knowledge", "green", f"{snapshot.discoveries} discoveries")
        if snapshot.knowledge_graph is not None
        else HealthSignal("Knowledge", "yellow", "no graph")
    )
    research = (
        HealthSignal("Research", "green", "report ready")
        if snapshot.research_report is not None
        else HealthSignal("Research", "yellow", "idle")
    )
    consensus = (
        HealthSignal("Consensus", "green", f"{snapshot.consensus_confidence:.0f}%")
        if snapshot.consensus_decision is not None
        else HealthSignal("Consensus", "yellow", "idle")
    )
    ordered = {
        "Federation": federation,
        "Graph": graph,
        "Scheduler": scheduler,
        "Twin": twin,
        "Knowledge": knowledge,
        "Research": research,
        "Consensus": consensus,
    }
    return tuple(ordered[name] for name in _DEFAULT_NAMES)
