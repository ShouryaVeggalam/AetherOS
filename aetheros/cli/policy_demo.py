"""CLI demo for Phase 2 policy recommendations (read-only).

Fetches one live telemetry sample, evaluates policy rules, and prints
advice. Never executes recommended actions.
"""

from __future__ import annotations

import argparse

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.policy_engine import PolicyEngine, PolicyRecommendation, TelemetrySnapshot
from aetheros.telemetry import TelemetryEngine


def _level_style(level: str) -> str:
    """Map severity level to a Rich style name."""

    if level == "critical":
        return "bold red"
    if level == "warning":
        return "bold yellow"
    return "bold green"


def format_status(snapshot: TelemetrySnapshot) -> Table:
    """Build a status table from a TelemetrySnapshot."""

    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("CPU", f"{snapshot.cpu_percent:.0f}%")
    table.add_row("Memory", f"{snapshot.memory_percent:.0f}%")
    table.add_row("Disk", f"{snapshot.disk_percent:.0f}%")
    if snapshot.battery_percent is not None:
        table.add_row("Battery", f"{snapshot.battery_percent:.0f}%")
    table.add_row("Processes", str(snapshot.process_count))
    return table


def format_recommendation(rec: PolicyRecommendation) -> Text:
    """Render one recommendation as styled text."""

    text = Text()
    text.append(f"{rec.level.upper()} — {rec.title}\n", style=_level_style(rec.level))
    text.append(f"Reason: {rec.reason}\n")
    text.append(f"Recommended action: {rec.recommended_action}\n")
    text.append(f"Confidence: {rec.confidence}%")
    return text


def render_report(
    snapshot: TelemetrySnapshot,
    recommendations: list[PolicyRecommendation],
) -> None:
    """Print system status and recommendations to the terminal."""

    console = Console()
    console.print(Panel(format_status(snapshot), title="System Status", border_style="cyan"))

    issues = [r for r in recommendations if r.level in ("warning", "critical")]
    if not issues:
        console.print(
            Panel(
                Text("System healthy.\nNo action recommended.", style="green"),
                title="Recommendations",
                border_style="green",
            )
        )
        return

    body = Text()
    for index, rec in enumerate(issues):
        if index:
            body.append("\n\n")
        body.append_text(format_recommendation(rec))
    console.print(Panel(body, title="Recommendations", border_style="red"))


def run_demo() -> None:
    """Collect one live sample, evaluate policy, and print the report."""

    telemetry = TelemetryEngine(interval_seconds=1.0)
    # Prime CPU counters, then take a real sample.
    telemetry.collect_once()
    system = telemetry.collect_once()
    snapshot = TelemetrySnapshot.from_system_snapshot(system)
    recommendations = PolicyEngine().evaluate_all(snapshot)
    render_report(snapshot, recommendations)


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser for the policy demo."""

    return argparse.ArgumentParser(
        prog="aetheros-policy",
        description="AetherOS Phase 2 — policy recommendations (no execution)",
    )


def main() -> None:
    """CLI entry point for the policy demo."""

    build_parser().parse_args()
    run_demo()


if __name__ == "__main__":
    main()
