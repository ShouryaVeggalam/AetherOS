"""Horizon Digital Twin — Infrastructure Twin scenario / diff / risk view.

Consumes TwinRun / InfrastructureSnapshot. Simulation display only.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.horizon.snapshot import HorizonSnapshot
from aetheros.horizon.widgets.table import HorizonTable


def render_twin(snapshot: HorizonSnapshot) -> RenderableType:
    """Render Infrastructure Digital Twin presentation from snapshot fields."""

    run = snapshot.twin_run
    baseline = snapshot.twin_snapshot
    scenarios = tuple(snapshot.twin_scenarios or ())
    scenario_name = snapshot.twin_scenario_name or "—"

    if run is None and baseline is None and not scenarios:
        body = Text(
            "DIGITAL TWIN idle.\nNo twin run in snapshot.\n"
            "Read-only · Simulation Only.",
            style="dim",
        )
        return Panel(
            body, title="Horizon · Digital Twin", border_style="bright_magenta"
        )

    library_rows = tuple(
        (
            str(getattr(s, "name", getattr(s, "id", "?"))),
            str(getattr(s, "description", ""))[:48] or "—",
        )
        for s in scenarios[:8]
    )
    library = HorizonTable(
        columns=("Scenario", "Description"),
        rows=library_rows,
    )

    current_line = _topology_line(baseline)
    after = getattr(run, "after", None) if run is not None else None
    simulated_line = _topology_line(after)
    result = getattr(run, "result", None) if run is not None else None
    diff = getattr(run, "diff", None) if run is not None else None
    if run is not None and scenario_name == "—":
        scenario_name = str(getattr(getattr(run, "scenario", None), "name", "—"))

    stability = "—"
    risk = "—"
    reasoning = "—"
    if result is not None:
        stability = f"{float(getattr(result, 'stability', 0.0)):.0f}"
        risk = str(getattr(result, "risk", "—"))
        reasoning = str(
            getattr(result, "explanation", getattr(result, "reasoning", "—"))
        )

    diff_lines: list[Text] = []
    if diff is None:
        diff_lines.append(Text("  (no diff)", style="dim"))
    else:
        added = tuple(getattr(diff, "added", ()) or ())
        removed = tuple(getattr(diff, "removed", ()) or ())
        changed = tuple(getattr(diff, "changed", ()) or ())
        if not (added or removed or changed):
            diff_lines.append(Text(f"  {diff}", style="dim"))
        else:
            if added:
                diff_lines.append(Text(f"  +{len(added)} nodes", style="bright_green"))
            if removed:
                diff_lines.append(Text(f"  −{len(removed)} nodes", style="bright_red"))
            if changed:
                diff_lines.append(
                    Text(f"  ~{len(changed)} changed", style="bright_yellow")
                )

    body = Group(
        Text("INFRASTRUCTURE DIGITAL TWIN", style="bold bright_magenta"),
        Text("Scenario library · read-only simulation view", style="dim"),
        Text(""),
        Text("Scenario Library", style="bold"),
        Text(""),
        library if library_rows else Text("  (empty)", style="dim"),
        Text(""),
        Text("Active Scenario", style="bold"),
        Text(f"  {scenario_name}"),
        Text(""),
        Text("Current Infrastructure", style="bold"),
        Text(current_line),
        Text(""),
        Text("Simulated Infrastructure", style="bold"),
        Text(simulated_line),
        Text(""),
        Text("Diff", style="bold"),
        *diff_lines,
        Text(""),
        Text("Stability", style="bold"),
        Text(f"  {stability}"),
        Text(""),
        Text("Risk", style="bold"),
        Text(f"  {risk}"),
        Text(""),
        Text("Reasoning", style="bold"),
        Text(f"  {reasoning}", style="dim"),
    )
    return Panel(body, title="Horizon · Digital Twin", border_style="bright_magenta")


def _topology_line(snap: object | None) -> str:
    if snap is None:
        return "  —"
    count = getattr(snap, "node_count", None)
    if count is None:
        topo = tuple(getattr(snap, "topology", ()) or ())
        count = len(topo)
    available = getattr(snap, "available_nodes", None)
    regions = tuple(getattr(snap, "regions", ()) or ())
    return (
        f"  nodes={count}  available={available if available is not None else '—'}  "
        f"regions={len(regions)}"
    )
