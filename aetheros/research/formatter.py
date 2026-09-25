"""Rich formatter for P9 Research Intelligence reports."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.research.models import SystemResearchReport


@dataclass(frozen=True, slots=True)
class ResearchIntelligencePanel:
    """Center-panel renderable for system research reports (shortcut X)."""

    report: SystemResearchReport | None
    view: str = "daily"

    def __rich__(self) -> RenderableType:
        """Render research report summary matching the P9 Rich example."""

        if self.report is None:
            return Panel(
                Text(
                    "RESEARCH REPORT idle.\n"
                    "Press X after telemetry and graph evidence are available.\n"
                    "A remains autonomous strategy research.\n"
                    "Status: Research Grade — evidence only",
                    style="dim",
                ),
                title="Research Intelligence",
                border_style="bright_cyan",
            )
        report = self.report
        top = report.discoveries[0] if report.discoveries else None
        date = report.generated_at.date().isoformat()
        body_parts: list[Text] = [
            Text("RESEARCH REPORT", style="bold bright_cyan"),
            Text(""),
            Text("Date", style="bold"),
            Text(f"  {date}"),
            Text(""),
            Text("Context", style="bold"),
            Text(f"  {report.context}"),
            Text(""),
            Text("View", style="bold"),
            Text(f"  {self.view}"),
            Text(""),
            Text("Observations", style="bold"),
            Text(f"  {len(report.observations)}"),
            Text(""),
            Text("Verified Discoveries", style="bold"),
            Text(f"  {len(report.discoveries)}"),
            Text(""),
        ]
        if top is not None:
            body_parts.extend(
                [
                    Text("Top Discovery", style="bold"),
                    Text(f"  {top.title}"),
                    Text(""),
                    Text("Evidence", style="bold"),
                    Text(f"  {top.evidence_count} sessions"),
                    Text(""),
                    Text("Reasoning", style="bold"),
                    Text("  Verified"),
                    Text(""),
                    Text("Confidence", style="bold"),
                    Text(f"  {top.confidence:.0f}%"),
                    Text(""),
                ]
            )
        else:
            body_parts.extend(
                [
                    Text("Top Discovery", style="bold"),
                    Text("  — (gates not cleared)"),
                    Text(""),
                ]
            )
        if report.bottlenecks:
            bn = report.bottlenecks[0]
            body_parts.extend(
                [
                    Text("Top Bottleneck", style="bold"),
                    Text(f"  {bn.title}"),
                    Text(f"  paths: {len(bn.graph_paths)}", style="dim"),
                    Text(""),
                ]
            )
        body_parts.extend(
            [
                Text("Status", style="bold"),
                Text("  Research Grade"),
                Text(""),
                Text(report.conclusion, style="dim"),
            ]
        )
        return Panel(
            Group(*body_parts),
            title="Research Intelligence",
            border_style="bright_cyan",
        )
