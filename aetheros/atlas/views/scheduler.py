"""Atlas Scheduler — candidate placements, scores, trade-offs (simulation only).

Consumes ScheduleResult. Never executes workloads.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.atlas.snapshot import AtlasSnapshot
from aetheros.atlas.widgets.progress_bar import AtlasProgressBar
from aetheros.atlas.widgets.table import AtlasTable


def render_scheduler(snapshot: AtlasSnapshot) -> RenderableType:
    """Render scheduler recommendations from an immutable ScheduleResult."""

    result = snapshot.schedule_result
    workload = snapshot.schedule_workload
    if result is None:
        body = Text(
            "SCHEDULER idle.\nNo ScheduleResult in snapshot.\n"
            "Simulation Only · never executes workloads.",
            style="dim",
        )
        return Panel(body, title="Atlas · Scheduler", border_style="bright_magenta")

    plans = tuple(getattr(result, "plans", ()) or ())
    rows = tuple(
        (
            str(getattr(plan, "target_node", "?")),
            f"{float(getattr(plan, 'score', 0.0)):.1f}",
            f"{float(getattr(plan, 'predicted_latency_ms', 0.0)):.1f} ms",
            f"{float(getattr(plan, 'predicted_cpu', 0.0)):.0f}%",
            f"{float(getattr(plan, 'predicted_memory', 0.0)):.0f}%",
        )
        for plan in plans
    )
    table = AtlasTable(
        columns=("Node", "Score", "Latency", "CPU", "Memory"),
        rows=rows,
    )
    best = getattr(result, "best_plan", None)
    trade_offs = tuple(getattr(result, "trade_offs", ()) or ())
    trade_lines: list[Text] = []
    if not trade_offs:
        trade_lines.append(Text("  (none)", style="dim"))
    for item in trade_offs:
        trade_lines.append(
            Text(
                f"  · vs {getattr(item, 'versus_node', '?')}  "
                f"(Δ {float(getattr(item, 'score_delta', 0.0)):.1f})"
            )
        )
        summary = str(getattr(item, "summary", "")).strip()
        if summary:
            trade_lines.append(Text(f"    {summary}", style="dim"))

    wl_name = getattr(workload, "name", "—") if workload is not None else "—"
    conf = float(getattr(result, "confidence", 0.0))
    body = Group(
        Text("DISTRIBUTED SCHEDULER", style="bold bright_magenta"),
        Text("Simulation Only · recommendations only", style="dim"),
        Text(""),
        Text("Workload", style="bold"),
        Text(f"  {wl_name}"),
        Text(""),
        Text("Candidates", style="bold"),
        Text(""),
        table if rows else Text("  (none)", style="dim"),
        Text(""),
        Text("Best Plan", style="bold"),
        Text(f"  {getattr(best, 'target_node', '—') if best is not None else '—'}"),
        Text(""),
        AtlasProgressBar(
            "Conf",
            conf,
        ),
        Text(""),
        Text("Trade-offs", style="bold"),
        *trade_lines,
    )
    return Panel(body, title="Atlas · Scheduler", border_style="bright_magenta")
