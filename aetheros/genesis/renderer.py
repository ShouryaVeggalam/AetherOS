"""Genesis Rich panel — knowledge, experiments, discoveries.

Presentation only. No research logic here.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.genesis.runtime import GenesisReport


@dataclass(frozen=True, slots=True)
class GenesisPanel:
    """Center-panel renderable for Genesis intelligence."""

    report: GenesisReport | None

    def __rich__(self) -> RenderableType:
        """Render the Genesis research overview."""

        if self.report is None:
            return Panel(
                Text(
                    "Genesis idle.\n"
                    "Press G for Genesis research layer.\n"
                    "Research only — humans approve recommendations.",
                    style="dim",
                ),
                title="Genesis",
                border_style="bright_yellow",
            )
        report = self.report
        census = report.census
        conf_pct = int(round(report.largest_confidence * 100))
        body = Group(
            Text("GENESIS", style="bold bright_yellow"),
            Text("Intelligence Layer — Research Only", style="dim"),
            Text(""),
            Text(f"Verified Knowledge    {census.verified_knowledge}", style="bold"),
            Text(f"Active Experiments    {census.active_experiments}"),
            Text(""),
            Text("Largest Evidence Set", style="bold cyan"),
            Text(f"  {report.largest_title}"),
            Text(f"  Simulations  {report.largest_simulations:,}"),
            Text(f"  Confidence   {conf_pct}%"),
            Text(""),
            _knowledge_table(report),
            Text(""),
            _experiments_table(report),
            Text(""),
            _discoveries(report),
            Text(""),
            _rejected(report),
            Text(""),
            _evidence_graph(report),
            Text(""),
            Text(f"Question: {report.question}", style="dim"),
            Text(report.status, style="dim italic"),
            Text(""),
            Text("G/ESC leave  ·  K cognitive  ·  research only", style="dim"),
        )
        return Panel(body, title="Genesis", border_style="bright_yellow")


def _knowledge_table(report: GenesisReport) -> Table:
    """Local knowledge base samples."""

    table = Table(title="Knowledge Base", expand=True, pad_edge=False)
    table.add_column("Statement")
    table.add_column("Sims", justify="right", width=8)
    table.add_column("Conf", justify="right", width=6)
    for record in report.knowledge[:4]:
        table.add_row(
            record.statement[:64] + ("…" if len(record.statement) > 64 else ""),
            f"{record.simulation_count:,}",
            f"{record.confidence:.0%}",
        )
    if not report.knowledge:
        table.add_row("—", "—", "—")
    return table


def _experiments_table(report: GenesisReport) -> Table:
    """Active / completed experiment scores."""

    table = Table(title="Active Experiments", expand=True, pad_edge=False)
    table.add_column("Experiment")
    table.add_column("Perf", justify="right")
    table.add_column("Stab", justify="right")
    table.add_column("Eff", justify="right")
    table.add_column("Fair", justify="right")
    for exp in report.experiments[:5]:
        table.add_row(
            exp.title,
            f"{exp.performance:.0f}",
            f"{exp.stability:.0f}",
            f"{exp.efficiency:.0f}",
            f"{exp.fairness:.0f}",
        )
    if not report.experiments:
        table.add_row("—", "—", "—", "—", "—")
    return table


def _discoveries(report: GenesisReport) -> Group:
    """Verified discoveries / theorems."""

    lines: list[Text] = [Text("Verified Discoveries", style="bold cyan")]
    if not report.theorems:
        lines.append(Text("  None yet.", style="dim"))
    for thm in report.theorems[:4]:
        lines.append(
            Text(
                f"  • {thm.title} ({thm.confidence:.0%}, "
                f"{thm.simulation_count:,} sims)"
            )
        )
    return Group(*lines)


def _rejected(report: GenesisReport) -> Group:
    """Archived rejected hypotheses."""

    lines: list[Text] = [Text("Rejected Hypotheses", style="bold cyan")]
    if not report.rejected:
        lines.append(Text("  None archived this cycle.", style="dim"))
    for outcome in report.rejected[:4]:
        lines.append(Text(f"  • {outcome.hypothesis.title}: {outcome.reason[:72]}"))
    return Group(*lines)


def _evidence_graph(report: GenesisReport) -> Group:
    """Ontology evidence edges."""

    lines: list[Text] = [Text("Evidence Graph", style="bold cyan")]
    for src, rel, dst in report.evidence_edges[:6]:
        lines.append(Text(f"  {src} —{rel}→ {dst}"))
    if not report.evidence_edges:
        lines.append(Text("  (empty)", style="dim"))
    return Group(*lines)
