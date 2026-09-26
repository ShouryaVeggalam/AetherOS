"""Horizon Scheduler — Planetary / Worldwide placement recommendations.

Consumes ScheduleDecision. Simulation Only · never executes workloads.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.horizon.snapshot import HorizonSnapshot
from aetheros.horizon.widgets.table import HorizonTable


def render_scheduler(snapshot: HorizonSnapshot) -> RenderableType:
    """Render planetary scheduler recommendations from an immutable decision."""

    decision = snapshot.schedule_decision
    workload = snapshot.schedule_workload
    if decision is None:
        body = Text(
            "WORLDWIDE SCHEDULER idle.\nNo ScheduleDecision in snapshot.\n"
            "Simulation Only · never deploys workloads.",
            style="dim",
        )
        return Panel(
            body, title="Horizon · Worldwide Scheduler", border_style="bright_cyan"
        )

    best = getattr(decision, "best_candidate", None)
    alternatives = tuple(getattr(decision, "alternatives", ()) or ())
    ranked = ((best,) if best is not None else ()) + alternatives
    ranked = ranked[:5]
    rows = tuple(
        (
            str(getattr(c, "region", "?")),
            str(getattr(c, "cluster", "?")),
            f"{float(getattr(c, 'score', 0.0)):.1f}",
            f"{float(getattr(c, 'latency_ms', 0.0)):.0f} ms",
            f"{float(getattr(c, 'availability', 0.0)):.2f}%",
            str(getattr(c, "trade_off", "") or "—"),
        )
        for c in ranked
        if c is not None
    )
    table = HorizonTable(
        columns=("Region", "Cluster", "Score", "Latency", "Avail", "Trade-off"),
        rows=rows,
    )
    wl_name = getattr(workload, "name", "—") if workload is not None else "—"
    conf = float(getattr(decision, "confidence", 0.0))
    body = Group(
        Text("WORLDWIDE SCHEDULER", style="bold bright_cyan"),
        Text("Simulation Only · recommendations only", style="dim"),
        Text(""),
        Text("Top Workload", style="bold"),
        Text(f"  {wl_name}"),
        Text(""),
        Text("Top 5 Candidates", style="bold"),
        Text(""),
        table if rows else Text("  (none)", style="dim"),
        Text(""),
        Text("Latency", style="bold"),
        Text(
            f"  {float(getattr(best, 'latency_ms', 0.0)):.0f} ms"
            if best is not None
            else "  —"
        ),
        Text(""),
        Text("Availability", style="bold"),
        Text(
            f"  {float(getattr(best, 'availability', 0.0)):.2f}%"
            if best is not None
            else "  —"
        ),
        Text(""),
        Text("Confidence", style="bold"),
        Text(f"  {conf:.0f}%"),
        Text(""),
        Text("Status", style="bold"),
        Text("  Simulation Only"),
    )
    return Panel(
        body, title="Horizon · Worldwide Scheduler", border_style="bright_cyan"
    )
