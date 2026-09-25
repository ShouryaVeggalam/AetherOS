"""Cognitive Graph Rich panel — causal graph, hypotheses, evidence.

Presentation only. No reasoning logic here.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.reasoning.explain import CognitiveReport


@dataclass(frozen=True, slots=True)
class CognitivePanel:
    """Center-panel renderable for cognitive operating intelligence."""

    report: CognitiveReport | None

    def __rich__(self) -> RenderableType:
        """Render the cognitive graph view."""

        if self.report is None:
            return Panel(
                Text(
                    "Cognitive engine idle.\n"
                    "Press G after telemetry is flowing.\n"
                    "Recommendation only — humans approve actions.",
                    style="dim",
                ),
                title="Cognitive Graph",
                border_style="bright_magenta",
            )
        report = self.report
        body = Group(
            Text("COGNITIVE OPERATING INTELLIGENCE", style="bold bright_magenta"),
            Text(""),
            Text("Observation", style="bold cyan"),
            Text(f"  {report.observation.summary}"),
            Text(""),
            _graph_summary(report),
            Text(""),
            _hypotheses(report),
            Text(""),
            _verified(report),
            Text(""),
            _plans(report),
            Text(""),
            _narrative(report),
            Text(""),
            _confidence(report.confidence),
            Text(""),
            Text(report.status, style="dim italic"),
            Text(""),
            Text("K/ESC leave  ·  systems reasoning  ·  not an LLM", style="dim"),
        )
        return Panel(body, title="Cognitive Graph", border_style="bright_magenta")


def _graph_summary(report: CognitiveReport) -> Group:
    """Compact causal graph stats + sample edges."""

    graph = report.graph
    lines: list[Text] = [
        Text("Causal Graph", style="bold cyan"),
        Text(f"  Nodes: {len(graph.nodes)}  Edges: {len(graph.edges)}"),
    ]
    for edge in graph.edges[:6]:
        src = graph.node(edge.source_id)
        dst = graph.node(edge.target_id)
        s_label = src.label if src else edge.source_id
        d_label = dst.label if dst else edge.target_id
        lines.append(
            Text(f"  {s_label} —{edge.relation}→ {d_label} " f"({edge.weight:.2f})")
        )
    return Group(*lines)


def _hypotheses(report: CognitiveReport) -> Group:
    """Active hypotheses table."""

    table = Table(title="Active Hypotheses", expand=True, pad_edge=False)
    table.add_column("Hypothesis")
    table.add_column("P", justify="right", width=6)
    hyps = report.hypotheses.hypotheses
    if not hyps:
        table.add_row("—", "—")
    for hyp in hyps[:5]:
        table.add_row(hyp.title, f"{hyp.probability:.0%}")
    return Group(table)


def _verified(report: CognitiveReport) -> Group:
    """Verified explanation block."""

    lines: list[Text] = [Text("Verified Explanation", style="bold cyan")]
    if report.verified.result is None:
        lines.append(Text("  None verified yet.", style="dim"))
        return Group(*lines)
    hyp = report.verified.result.hypothesis
    lines.append(Text(f"  {hyp.title}", style="bold green"))
    lines.append(Text(f"  {hyp.description}"))
    lines.append(Text("Evidence Chain", style="bold cyan"))
    for reason in report.verified.result.reasons[:5]:
        lines.append(Text(f"  • {reason}"))
    return Group(*lines)


def _plans(report: CognitiveReport) -> Group:
    """Recommended intervention plan."""

    lines: list[Text] = [Text("Plans", style="bold cyan")]
    if report.plans is None or report.plans.recommended is None:
        lines.append(
            Text("  No intervention plan (system stable or unverified).", style="dim")
        )
        return Group(*lines)
    rec = report.plans.recommended
    lines.append(Text(f"  Recommended: {rec.title} (score {rec.score})"))
    for plan in report.plans.plans[:3]:
        lines.append(Text(f"  • {plan.title}: {plan.score}"))
    return Group(*lines)


def _narrative(report: CognitiveReport) -> Group:
    """Research-quality narrative lines."""

    lines: list[Text] = [Text("Reasoning", style="bold cyan")]
    for line in report.narrative[:8]:
        lines.append(Text(f"  {line}"))
    return Group(*lines)


def _confidence(confidence: int) -> Group:
    """Confidence gauge."""

    width = 20
    filled = int(round((confidence / 100.0) * width))
    bar = "█" * filled + "░" * (width - filled)
    style = "green" if confidence >= 70 else "yellow" if confidence >= 40 else "red"
    return Group(
        Text("Confidence", style="bold cyan"),
        Text(f"{bar}  {confidence}%", style=style),
    )
