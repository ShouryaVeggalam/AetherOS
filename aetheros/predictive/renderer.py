"""Rich renderer for Predictive Intelligence panels.

Presentation only. No forecasting math lives here.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.predictive.models import Forecast, PredictiveReport, Trend

_ARROWS = {
    "rising": "Rising ↗",
    "stable": "Stable →",
    "falling": "Falling ↘",
    "volatile": "Volatile ↔",
}


@dataclass(frozen=True, slots=True)
class PredictivePanel:
    """Center-panel renderable for one PredictiveReport."""

    report: PredictiveReport | None

    def __rich__(self) -> RenderableType:
        """Render the predictive intelligence view."""

        if self.report is None:
            return Panel(
                Text(
                    "Collecting history…\n"
                    "Need a few telemetry samples before forecasts appear.\n"
                    "Press P after Observatory has recorded data.",
                    style="dim",
                ),
                title="Predictive Intelligence",
                border_style="yellow",
            )
        report = self.report
        body = Group(
            Text("PREDICTIVE INTELLIGENCE", style="bold yellow"),
            Text(""),
            _cpu_block(report),
            Text(""),
            _trend_block(report.trends),
            Text(""),
            _confidence_block(report),
            Text(""),
            _stability_risk(report),
            Text(""),
            _anomaly_block(report),
            Text(""),
            _explain_block(report),
            Text(""),
            Text("P/ESC leave  ·  statistical only  ·  no ML", style="dim"),
        )
        return Panel(body, title="Predictive Intelligence", border_style="yellow")


def _cpu_block(report: PredictiveReport) -> Group:
    """Render Now / +5m / +15m / +60m CPU table."""

    by_h = {f.horizon: f for f in report.forecasts}
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("label", style="bold cyan", width=8)
    table.add_column("value", justify="right")
    table.add_row("Now", f"{report.now_cpu:.0f}%")
    for horizon in (5, 15, 60):
        forecast = by_h.get(horizon)  # type: ignore[arg-type]
        value = f"{forecast.predicted_cpu:.0f}%" if forecast else "—"
        table.add_row(f"+{horizon}m", value)
    return Group(Text("CPU", style="bold cyan"), table)


def _trend_block(trends: tuple[Trend, ...]) -> Group:
    """Render trend arrows for each metric."""

    lines = [Text("Trend", style="bold cyan")]
    if not trends:
        lines.append(Text("—", style="dim"))
        return Group(*lines)
    for trend in trends:
        if trend.metric == "battery" and trend.volatility == 0 and trend.slope == 0:
            continue
        label = _ARROWS.get(trend.direction, trend.direction)
        lines.append(
            Text(f"  {trend.metric.upper():<7} {label}  ({trend.slope:+.2f}%/min)")
        )
    return Group(*lines)


def _confidence_block(report: PredictiveReport) -> Group:
    """Render average confidence gauge from forecasts."""

    if report.forecasts:
        conf = int(
            round(sum(f.confidence for f in report.forecasts) / len(report.forecasts))
        )
    else:
        conf = 0
    width = 20
    filled = int(round((conf / 100.0) * width))
    bar = "█" * filled + "░" * (width - filled)
    style = "green" if conf >= 70 else "yellow" if conf >= 40 else "red"
    return Group(
        Text("Confidence", style="bold cyan"),
        Text(f"{bar}  {conf}%", style=style),
    )


def _stability_risk(report: PredictiveReport) -> Group:
    """Render expected stability and risk level."""

    risk_style = {
        "low": "green",
        "medium": "yellow",
        "high": "red",
    }.get(report.risk, "white")
    return Group(
        Text("Expected Stability", style="bold cyan"),
        Text(f"  {report.expected_stability}/100"),
        Text("Risk", style="bold cyan"),
        Text(f"  {report.risk.upper()}", style=risk_style),
    )


def _anomaly_block(report: PredictiveReport) -> Group:
    """Render anomaly alerts when present."""

    lines = [Text("Anomalies", style="bold cyan")]
    if not report.anomalies:
        lines.append(Text("  None detected", style="dim"))
        return Group(*lines)
    for alert in report.anomalies[:4]:
        lines.append(Text(f"  • {alert.title}: {alert.description}"))
    return Group(*lines)


def _explain_block(report: PredictiveReport) -> Group:
    """Render explainability details for the forecast."""

    exp = report.explanation
    lines = [
        Text("Reason", style="bold cyan"),
        Text(f"  {exp.reason}"),
        Text(""),
        Text("Explainability", style="bold cyan"),
        Text(f"  Window: {exp.window_samples} samples / " f"{exp.window_seconds}s"),
        Text(f"  Method: {exp.method}"),
        Text(f"  {exp.confidence_summary}"),
    ]
    if exp.slope_summary:
        lines.append(Text(f"  Slope: {exp.slope_summary[0]}"))
    return Group(*lines)


def format_predictive_report(
    report: PredictiveReport | None,
) -> PredictivePanel:
    """Build a PredictivePanel from a report (or empty state)."""

    return PredictivePanel(report=report)


def forecast_by_horizon(
    forecasts: tuple[Forecast, ...],
    horizon: int,
) -> Forecast | None:
    """Lookup helper for tests and callers."""

    for item in forecasts:
        if item.horizon == horizon:
            return item
    return None
