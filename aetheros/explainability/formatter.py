"""Rich formatter for explainability panels.

Presentation only. No evidence collection or confidence math here.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.explainability.models import Evidence, Explanation, ReasoningChain


@dataclass(frozen=True, slots=True)
class ExplainabilityPanel:
    """Center-panel renderable for one Explanation."""

    explanation: Explanation | None

    def __rich__(self) -> RenderableType:
        """Render the explainability view as a Rich Panel."""

        if self.explanation is None:
            return Panel(
                Text(
                    "No decision to explain yet.\n"
                    "Wait for telemetry pressure or press E after a recommendation.",
                    style="dim",
                ),
                title="AI Explanation",
                border_style="magenta",
            )
        exp = self.explanation
        body = Group(
            _recommendation_block(exp.title),
            Text(""),
            _why_block(exp),
            Text(""),
            _confidence_gauge(exp.confidence),
            Text(""),
            _reasoning_sections(exp.reasoning_chain),
            Text(""),
            _conclusion_block(exp.summary),
            Text(""),
            _evidence_table(exp.evidence),
            Text(""),
            _sources_line(exp.evidence),
            Text(""),
            Text("E/ESC leave  ·  read-only evidence", style="dim"),
        )
        return Panel(body, title="AI Explanation", border_style="magenta")


def _recommendation_block(title: str) -> Text:
    """Render the recommendation header."""

    text = Text()
    text.append("Recommendation\n", style="bold cyan")
    text.append(title, style="bold white")
    return text


def _why_block(explanation: Explanation) -> Group:
    """Render Why? bullets from evidence descriptions (capped)."""

    lines = [Text("Why?", style="bold cyan")]
    bullets = [e.description for e in explanation.evidence[:6]]
    if not bullets:
        lines.append(Text("• No evidence collected yet.", style="dim"))
    for item in bullets:
        lines.append(Text(f"• {item}"))
    return Group(*lines)


def _confidence_gauge(confidence: int) -> Group:
    """Render a textual confidence gauge."""

    width = 20
    filled = int(round((confidence / 100.0) * width))
    bar = "█" * filled + "░" * (width - filled)
    style = "green" if confidence >= 70 else "yellow" if confidence >= 40 else "red"
    return Group(
        Text("Confidence", style="bold cyan"),
        Text(f"{bar}  {confidence}%", style=style),
    )


def _reasoning_sections(chain: ReasoningChain) -> Group:
    """Render the structured reasoning chain."""

    blocks: list[Text] = [Text("Reasoning Chain", style="bold cyan")]
    blocks.append(_section("Observation", chain.observations))
    blocks.append(_section("Historical Pattern", chain.historical_patterns))
    blocks.append(_section("Intent Context", chain.intent_context))
    blocks.append(_section("Simulation Support", chain.simulation_support))
    return Group(*blocks)


def _conclusion_block(summary: str) -> Text:
    """Render the final conclusion sentence."""

    text = Text()
    text.append("Final Conclusion\n", style="bold cyan")
    text.append(summary)
    return text


def _section(label: str, lines: tuple[str, ...]) -> Text:
    """One labeled reasoning subsection."""

    text = Text()
    text.append(f"{label}\n", style="bold")
    if not lines:
        text.append("  —\n", style="dim")
        return text
    for line in lines[:3]:
        text.append(f"  {line}\n")
    return text


def _evidence_table(evidence: tuple[Evidence, ...]) -> Table:
    """Evidence table with source, metric, value, description."""

    table = Table(title="Evidence Table", expand=True, pad_edge=False)
    table.add_column("Source", style="cyan", width=10)
    table.add_column("Metric", width=12)
    table.add_column("Value", justify="right", width=7)
    table.add_column("Detail", overflow="fold")
    if not evidence:
        table.add_row("—", "—", "—", "No evidence")
        return table
    for item in evidence[:10]:
        table.add_row(
            item.source,
            item.metric,
            f"{item.value:.0f}",
            item.description,
        )
    return table


def _sources_line(evidence: tuple[Evidence, ...]) -> Text:
    """List unique evidence source categories present."""

    order = ("telemetry", "history", "simulation", "intent")
    present = {e.source for e in evidence}
    text = Text()
    text.append("Evidence Sources\n", style="bold cyan")
    if not present:
        text.append("—", style="dim")
        return text
    labels = [name.capitalize() for name in order if name in present]
    text.append("  ".join(labels))
    return text


def format_explanation(explanation: Explanation | None) -> ExplainabilityPanel:
    """Build an ExplainabilityPanel from an Explanation (or empty state)."""

    return ExplainabilityPanel(explanation=explanation)
