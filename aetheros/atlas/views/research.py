"""Atlas Research — daily report, trends, discoveries, journal.

Consumes SystemResearchReport / journal entries. Evidence display only.
"""

from __future__ import annotations

from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.atlas.snapshot import AtlasSnapshot
from aetheros.atlas.widgets.stat_card import StatCard
from aetheros.atlas.widgets.table import AtlasTable


def render_research(snapshot: AtlasSnapshot) -> RenderableType:
    """Render research intelligence presentation from snapshot."""

    report = snapshot.research_report
    journal = snapshot.research_journal

    if report is None and not journal:
        body = Text(
            "RESEARCH idle.\nNo research report in snapshot.\n"
            "Evidence only · research grade.",
            style="dim",
        )
        return Panel(body, title="Atlas · Research", border_style="bright_cyan")

    discoveries = tuple(getattr(report, "discoveries", ()) or ()) if report else ()
    observations = tuple(getattr(report, "observations", ()) or ()) if report else ()
    trends = tuple(getattr(report, "trends", ()) or ()) if report else ()
    context = str(getattr(report, "context", "—")) if report else "—"
    generated = getattr(report, "generated_at", None) if report else None
    date = generated.date().isoformat() if generated is not None else "—"

    top = discoveries[0] if discoveries else None
    top_conf = (
        f"{float(getattr(top, 'confidence', 0.0)):.0f}%" if top is not None else "—"
    )
    evidence_count = 0
    if top is not None:
        evidence_count = len(tuple(getattr(top, "evidence", ()) or ()))
    if evidence_count == 0 and report is not None:
        evidence_count = len(observations)

    cards = Columns(
        [
            StatCard("Date", date, tone="bright_cyan"),
            StatCard("Discoveries", str(len(discoveries)), tone="bright_magenta"),
            StatCard("Evidence", str(evidence_count), tone="bright_white"),
            StatCard("Confidence", top_conf, tone="bright_green"),
        ],
        equal=True,
        expand=True,
    )

    discovery_rows = tuple(
        (
            str(getattr(d, "title", getattr(d, "summary", "discovery")))[:40],
            f"{float(getattr(d, 'confidence', 0.0)):.0f}%",
        )
        for d in discoveries[:8]
    )
    discovery_table = AtlasTable(
        columns=("Discovery", "Confidence"),
        rows=discovery_rows,
    )

    trend_lines: list[Text] = []
    if not trends:
        trend_lines.append(Text("  (none)", style="dim"))
    for trend in trends[:6]:
        trend_lines.append(Text(f"  · {trend}"))

    journal_lines: list[Text] = []
    if not journal:
        journal_lines.append(Text("  (none)", style="dim"))
    for entry in journal[:8]:
        journal_lines.append(
            Text(f"  · {getattr(entry, 'summary', getattr(entry, 'text', entry))}")
        )

    body = Group(
        Text("RESEARCH", style="bold bright_cyan"),
        Text("Daily report · weekly trends · discoveries", style="dim"),
        Text(""),
        Text("Context", style="bold"),
        Text(f"  {context}"),
        Text(""),
        cards,
        Text(""),
        Text("Discoveries", style="bold"),
        Text(""),
        discovery_table if discovery_rows else Text("  (none)", style="dim"),
        Text(""),
        Text("Weekly Trends", style="bold"),
        *trend_lines,
        Text(""),
        Text("Research Journal", style="bold"),
        *journal_lines,
    )
    return Panel(body, title="Atlas · Research", border_style="bright_cyan")
