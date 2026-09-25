"""Multi-Agent View Rich panel — agents, messages, coordinator decision.

Presentation only. No deliberation logic here.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.agents.report import AgenticReport


@dataclass(frozen=True, slots=True)
class MultiAgentPanel:
    """Center-panel renderable for agentic systems intelligence."""

    report: AgenticReport | None

    def __rich__(self) -> RenderableType:
        """Render the multi-agent collaboration view."""

        if self.report is None:
            return Panel(
                Text(
                    "Agentic layer idle.\n"
                    "Press M after telemetry is flowing.\n"
                    "Recommendation only — humans approve actions.",
                    style="dim",
                ),
                title="Multi-Agent View",
                border_style="bright_cyan",
            )
        report = self.report
        body = Group(
            Text("AGENTIC SYSTEMS INTELLIGENCE", style="bold bright_cyan"),
            Text(""),
            _agents_table(report),
            Text(""),
            _coordinator_block(report),
            Text(""),
            Text(
                f"Bus messages this session window: {report.message_count}",
                style="dim",
            ),
            Text(""),
            Text("M/ESC leave  ·  multi-agent  ·  no OS execution", style="dim"),
        )
        return Panel(body, title="Multi-Agent View", border_style="bright_cyan")


def _agents_table(report: AgenticReport) -> Table:
    """Agent status / latest message / confidence table."""

    table = Table(title="Agents", expand=True, pad_edge=False)
    table.add_column("Agent")
    table.add_column("Status", width=10)
    table.add_column("Latest Message")
    table.add_column("Conf", justify="right", width=6)
    for row in report.agents:
        mark = "✓" if row.status in ("ok", "warning") else "…"
        if row.status == "error":
            mark = "✗"
        style = (
            "green"
            if row.status == "ok"
            else "yellow" if row.status == "warning" else "dim"
        )
        table.add_row(
            f"{row.agent_id}",
            Text(f"{mark} {row.status}", style=style),
            row.latest_message[:72] or "—",
            f"{row.confidence:.0%}",
        )
    return table


def _coordinator_block(report: AgenticReport) -> Group:
    """Coordinator decision, confidence, reasoning."""

    decision = report.decision
    conf_pct = int(round(decision.confidence * 100))
    width = 20
    filled = int(round(decision.confidence * width))
    bar = "█" * filled + "░" * (width - filled)
    bar_style = "green" if conf_pct >= 70 else "yellow" if conf_pct >= 40 else "red"
    lines: list[Text] = [
        Text("Coordinator", style="bold cyan"),
        Text(f"Recommendation: {decision.recommendation}", style="bold"),
        Text(f"Confidence: {bar}  {conf_pct}%", style=bar_style),
        Text(""),
        Text("Reasoning", style="bold cyan"),
        Text(f"  {decision.reasoning}"),
    ]
    if decision.supporting_agents:
        lines.append(
            Text(
                "Supporting: " + ", ".join(decision.supporting_agents),
                style="dim",
            )
        )
    if decision.conflicting_agents:
        lines.append(
            Text(
                "Conflict resolved: " + ", ".join(decision.conflicting_agents),
                style="yellow",
            )
        )
    return Group(*lines)
