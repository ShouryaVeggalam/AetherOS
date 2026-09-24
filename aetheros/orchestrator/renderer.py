"""Rich renderer for the Workload Planner panel.

Presentation only. No planning or scoring logic here.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.orchestrator.models import ExecutionPlan, WorkloadProfile
from aetheros.orchestrator.workload import all_workloads


@dataclass(frozen=True, slots=True)
class WorkloadPlannerPanel:
    """Center-panel renderable for the orchestrator planner."""

    plan: ExecutionPlan | None
    selected: WorkloadProfile | None = None

    def __rich__(self) -> RenderableType:
        """Render the workload planner view."""

        workload = self.selected or (self.plan.workload if self.plan else None)
        if self.plan is None or workload is None:
            return Panel(
                Text(
                    "Collect cluster nodes, then press W.\n"
                    "Tab/] cycles workloads. Recommendation only.",
                    style="dim",
                ),
                title="Workload Planner",
                border_style="green",
            )
        plan = self.plan
        body = Group(
            Text("WORKLOAD PLANNER", style="bold green"),
            Text(""),
            _workload_block(workload),
            Text(""),
            _recommended(plan),
            Text(""),
            _scores_table(plan),
            Text(""),
            _rejected(plan),
            Text(""),
            _reasoning(plan),
            Text(""),
            Text(plan.status, style="dim italic"),
            Text(""),
            Text(
                "W/ESC leave  ·  ] next workload  ·  recommendation only",
                style="dim",
            ),
        )
        return Panel(body, title="Workload Planner", border_style="green")


def _workload_block(workload: WorkloadProfile) -> Group:
    """Render selected workload and catalog hint."""

    names = " · ".join(w.name for w in all_workloads())
    return Group(
        Text("Workload", style="bold cyan"),
        Text(f"  {workload.name}", style="bold white"),
        Text(f"  {workload.description}", style="dim"),
        Text(f"  Catalog: {names}", style="dim"),
    )


def _recommended(plan: ExecutionPlan) -> Group:
    """Render recommended node and score."""

    if plan.recommended_node is None:
        return Group(
            Text("Recommended", style="bold cyan"),
            Text("  None — all nodes rejected or unavailable.", style="red"),
            Text("Score", style="bold cyan"),
            Text("  0"),
        )
    node = plan.recommended_node
    return Group(
        Text("Recommended", style="bold cyan"),
        Text(f"  {node.hostname}", style="bold green"),
        Text("Score", style="bold cyan"),
        Text(f"  {plan.score}"),
    )


def _scores_table(plan: ExecutionPlan) -> Group:
    """Render cluster suitability scores."""

    table = Table(title="Cluster Scores", expand=True, pad_edge=False)
    table.add_column("Node", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("CPU", justify="right")
    table.add_column("Mem", justify="right")
    table.add_column("GPU", justify="right")
    if not plan.ranked:
        table.add_row("—", "—", "—", "—", "—")
    for item in plan.ranked:
        table.add_row(
            item.node.hostname,
            str(item.score),
            f"{item.node.cpu:.0f}%",
            f"{item.node.memory:.0f}%",
            f"{item.node.gpu:.0f}",
        )
    return Group(table)


def _rejected(plan: ExecutionPlan) -> Group:
    """Render rejected nodes with reasons."""

    lines: list[Text] = [Text("Rejected", style="bold cyan")]
    if not plan.rejected_nodes:
        lines.append(Text("  None", style="dim"))
        return Group(*lines)
    for item in plan.rejected_nodes[:8]:
        lines.append(Text(f"  {item.hostname:<12} {item.reason}"))
    return Group(*lines)


def _reasoning(plan: ExecutionPlan) -> Group:
    """Render explanation bullets."""

    lines: list[Text] = [Text("Reasoning", style="bold cyan")]
    for line in plan.explanation[:10]:
        lines.append(Text(f"  {line}"))
    return Group(*lines)
