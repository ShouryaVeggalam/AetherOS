"""Horizon Research — daily report, trends, discoveries, journal.

Consumes research report / journal / discoveries. Presentation only.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.horizon.snapshot import HorizonSnapshot
from aetheros.horizon.widgets.timeline import Timeline


def render_research(snapshot: HorizonSnapshot) -> RenderableType:
    """Render research intelligence presentation from snapshot fields."""

    report = snapshot.research_report
    journal = tuple(snapshot.research_journal or ())
    discoveries = tuple(snapshot.research_discoveries or ())

    if report is None and not journal and not discoveries:
        body = Text(
            "RESEARCH idle.\nNo research report in snapshot.\nRead-only.",
            style="dim",
        )
        return Panel(body, title="Horizon · Research", border_style="bright_magenta")

    title = str(getattr(report, "title", "Daily Report")) if report else "Daily Report"
    summary = str(getattr(report, "summary", "—")) if report is not None else "—"
    trends = tuple(getattr(report, "weekly_trends", ()) or ()) if report else ()

    discovery_lines: list[Text] = []
    if not discoveries:
        discovery_lines.append(Text("  (none)", style="dim"))
    for item in discoveries:
        name = getattr(item, "name", item)
        conf = getattr(item, "confidence", None)
        suffix = f"  ({float(conf):.0f}%)" if conf is not None else ""
        discovery_lines.append(Text(f"  · {name}{suffix}"))

    events = tuple(
        (
            str(getattr(entry, "stamp", "—")),
            str(getattr(entry, "entry", getattr(entry, "text", "—"))),
        )
        for entry in journal
    )
    # Simulation evidence from twin timeline if journal empty.
    if not events and snapshot.timeline_events:
        events = snapshot.timeline_events

    body = Group(
        Text("RESEARCH", style="bold bright_magenta"),
        Text("Daily · weekly · discoveries · journal", style="dim"),
        Text(""),
        Text("Daily Report", style="bold"),
        Text(f"  {title}"),
        Text(f"  {summary}", style="dim"),
        Text(""),
        Text("Weekly Trends", style="bold"),
        *(
            [Text(f"  · {t}") for t in trends]
            if trends
            else [Text("  (none)", style="dim")]
        ),
        Text(""),
        Text("Discoveries", style="bold"),
        *discovery_lines,
        Text(""),
        Text("Research Journal", style="bold"),
        Text(""),
        Timeline(events=events),
        Text(""),
        Text("Simulation Evidence", style="bold"),
        Text(
            f"  active simulations: {snapshot.active_simulations}  ·  "
            f"twin scenario: {snapshot.twin_scenario_name or '—'}",
            style="dim",
        ),
    )
    return Panel(body, title="Horizon · Research", border_style="bright_magenta")
