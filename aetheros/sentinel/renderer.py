"""Sentinel Rich panel — anomalies, causes, cascade, recovery, score.

Presentation only. No detection logic here.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.sentinel.runtime import SentinelReport


@dataclass(frozen=True, slots=True)
class SentinelPanel:
    """Center-panel renderable for Sentinel intelligence fabric."""

    report: SentinelReport | None

    def __rich__(self) -> RenderableType:
        """Render the Sentinel overview."""

        if self.report is None:
            return Panel(
                Text(
                    "Sentinel idle.\n"
                    "Press S for resilience intelligence.\n"
                    "Recommendation only — humans approve recovery.",
                    style="dim",
                ),
                title="Sentinel",
                border_style="bright_red",
            )
        report = self.report
        conf_pct = int(round(report.confidence * 100))
        risk_style = {
            "Low": "green",
            "Medium": "yellow",
            "High": "red",
        }.get(report.risk, "white")
        body = Group(
            Text("SENTINEL", style="bold bright_red"),
            Text("Intelligence Fabric — Recommendation Only", style="dim"),
            Text(""),
            Text(f"Health     {report.health:.0f}", style="bold"),
            Text(f"Risk       {report.risk}", style=risk_style),
            Text(f"Active Anomalies  {len(report.anomalies)}"),
            Text(
                "Predicted Cascade  "
                + ("None" if not report.cascade.active else report.cascade.summary)
            ),
            Text(""),
            Text("Recommended Strategy", style="bold cyan"),
            Text(f"  {report.recommended_strategy}"),
            Text(f"  Confidence  {conf_pct}%"),
            Text(""),
            _anomalies(report),
            Text(""),
            _root_causes(report),
            Text(""),
            _cascade(report),
            Text(""),
            _recovery(report),
            Text(""),
            _resilience(report),
            Text(""),
            Text(report.status, style="dim italic"),
            Text(""),
            Text("S/ESC leave  ·  recommendation only", style="dim"),
        )
        return Panel(body, title="Sentinel", border_style="bright_red")


def _anomalies(report: SentinelReport) -> Table:
    """Live anomalies table."""

    table = Table(title="Live Anomalies", expand=True, pad_edge=False)
    table.add_column("Kind")
    table.add_column("Severity", width=8)
    table.add_column("Title")
    if not report.anomalies:
        table.add_row("—", "—", "None")
    for anomaly in report.anomalies[:6]:
        table.add_row(anomaly.kind, anomaly.severity, anomaly.title)
    return table


def _root_causes(report: SentinelReport) -> Group:
    """Root cause graph (ranked list)."""

    lines: list[Text] = [Text("Root Cause Graph", style="bold cyan")]
    if not report.root_causes:
        lines.append(Text("  No causes (system quiet).", style="dim"))
    for cause in report.root_causes[:4]:
        lines.append(
            Text(
                f"  #{cause.rank} {cause.title} ({cause.confidence:.0%}) — "
                f"{cause.explanation[:64]}"
            )
        )
    return Group(*lines)


def _cascade(report: SentinelReport) -> Group:
    """Cascade hops."""

    lines: list[Text] = [Text("Cascade Simulation", style="bold cyan")]
    if not report.cascade.active:
        lines.append(Text("  Predicted Cascade: None", style="dim"))
        return Group(*lines)
    lines.append(Text(f"  {report.cascade.summary}"))
    for hop in report.cascade.hops[:4]:
        lines.append(
            Text(f"  • {hop.entity_id}: {hop.stage} (pressure {hop.pressure:.0f})")
        )
    return Group(*lines)


def _recovery(report: SentinelReport) -> Group:
    """Recovery planner options."""

    lines: list[Text] = [Text("Recovery Planner", style="bold cyan")]
    if not report.recovery.strategies:
        lines.append(Text("  No strategies required.", style="dim"))
        return Group(*lines)
    for strategy in report.recovery.strategies[:4]:
        mark = "★" if report.recovery.recommended == strategy else "•"
        lines.append(
            Text(
                f"  {mark} {strategy.title}  score {strategy.score:.0f} "
                f"(conf {strategy.confidence:.0%})"
            )
        )
    return Group(*lines)


def _resilience(report: SentinelReport) -> Group:
    """Resilience score breakdown."""

    score = report.resilience
    return Group(
        Text("Resilience Score", style="bold cyan"),
        Text(
            f"  Health {score.health:.0f} · Stability {score.stability:.0f} · "
            f"Redundancy {score.redundancy:.0f} · Risk {score.risk}"
        ),
        Text(f"  {score.explanation}", style="dim"),
    )
