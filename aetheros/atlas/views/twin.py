"""Atlas Digital Twin — scenario, snapshots, diff, stability, risk.

Consumes DigitalTwinReport / TwinSnapshot. Simulation display only.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.atlas.snapshot import AtlasSnapshot


def render_twin(snapshot: AtlasSnapshot) -> RenderableType:
    """Render Digital Twin presentation from snapshot fields."""

    report = snapshot.twin_report
    baseline = snapshot.twin_baseline
    scenario = snapshot.twin_scenario_name or "—"

    if report is None and baseline is None:
        body = Text(
            "DIGITAL TWIN idle.\nNo twin report in snapshot.\n"
            "Read-only · Simulation Only.",
            style="dim",
        )
        return Panel(body, title="Atlas · Digital Twin", border_style="bright_magenta")

    result = getattr(report, "result", None) if report is not None else None
    diff = getattr(report, "diff", None) if report is not None else None
    base_tel = getattr(baseline, "telemetry", None) if baseline is not None else None
    if base_tel is None and report is not None:
        base_snap = getattr(report, "baseline", None)
        base_tel = (
            getattr(base_snap, "telemetry", None) if base_snap is not None else None
        )

    current_line = "  —"
    if base_tel is not None:
        current_line = (
            f"  CPU {float(getattr(base_tel, 'cpu_percent', 0)):.0f}%  "
            f"MEM {float(getattr(base_tel, 'memory_percent', 0)):.0f}%  "
            f"DISK {float(getattr(base_tel, 'disk_percent', 0)):.0f}%"
        )

    simulated_line = "  —"
    stability = "—"
    risk = "—"
    reasoning = "—"
    if result is not None:
        scenario = str(getattr(getattr(result, "scenario", None), "name", scenario))
        simulated_line = (
            f"  CPU {float(getattr(result, 'predicted_cpu', 0)):.0f}%  "
            f"MEM {float(getattr(result, 'predicted_memory', 0)):.0f}%  "
            f"DISK {float(getattr(result, 'predicted_disk', 0)):.0f}%"
        )
        stability = f"{float(getattr(result, 'stability', 0)):.0f}"
        risk = str(getattr(result, "risk", "—"))
        reasoning = str(getattr(result, "reasoning", "—"))

    diff_lines: list[Text] = []
    if diff is None:
        diff_lines.append(Text("  (no diff)", style="dim"))
    else:
        changes = tuple(getattr(diff, "changes", ()) or ())
        if not changes:
            # Fallback: string representation helpers if present
            metrics = tuple(getattr(diff, "metrics", ()) or ())
            if metrics:
                for metric in metrics:
                    diff_lines.append(Text(f"  {metric}"))
            else:
                diff_lines.append(Text(f"  {diff}", style="dim"))
        for change in changes:
            name = getattr(change, "name", getattr(change, "metric", "metric"))
            delta = getattr(change, "delta", getattr(change, "change", ""))
            diff_lines.append(Text(f"  {name}: {delta}"))

    body = Group(
        Text("DIGITAL TWIN", style="bold bright_magenta"),
        Text("Scenario selector · read-only simulation view", style="dim"),
        Text(""),
        Text("Scenario", style="bold"),
        Text(f"  {scenario}"),
        Text(""),
        Text("Current Snapshot", style="bold"),
        Text(current_line),
        Text(""),
        Text("Simulated Snapshot", style="bold"),
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
    return Panel(body, title="Atlas · Digital Twin", border_style="bright_magenta")
