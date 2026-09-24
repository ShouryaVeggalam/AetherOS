"""End-to-end demo: Telemetry → Policy → Safety (no OS execution).

Prints APPROVED or BLOCKED for each recommendation after safety checks.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.policy_engine import PolicyEngine, PolicyRecommendation, TelemetrySnapshot
from aetheros.safety import AuditLogger, CooldownManager, SafetyResult, SafetyValidator
from aetheros.telemetry import TelemetryEngine


def format_status(snapshot: TelemetrySnapshot) -> Table:
    """Build a compact system-status table."""

    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()
    table.add_row("CPU", f"{snapshot.cpu_percent:.0f}%")
    table.add_row("Memory", f"{snapshot.memory_percent:.0f}%")
    table.add_row("Disk", f"{snapshot.disk_percent:.0f}%")
    return table


def format_decision(
    recommendation: PolicyRecommendation,
    result: SafetyResult,
) -> Text:
    """Render one safety decision in the Phase-3 demo style."""

    text = Text()
    if result.status == "approved":
        text.append("APPROVED\n", style="bold green")
        text.append(f"Recommendation: {recommendation.title}\n")
        text.append(f"Reason: {result.reason}")
    elif result.status == "cooldown":
        text.append("BLOCKED\n", style="bold yellow")
        text.append(f"Recommendation: {recommendation.title}\n")
        text.append(f"Reason: {result.reason}")
    else:
        text.append("BLOCKED\n", style="bold red")
        text.append(f"Recommendation: {recommendation.title}\n")
        text.append(f"Reason: {result.reason}")
    return text


def render_pipeline(
    snapshot: TelemetrySnapshot,
    decisions: list[tuple[PolicyRecommendation, SafetyResult]],
    audit_path: Path,
) -> None:
    """Print the full Telemetry → Policy → Safety report."""

    console = Console()
    console.print(
        Panel(
            Text(
                "Telemetry Snapshot\n"
                "        ↓\n"
                "   Policy Engine\n"
                "        ↓\n"
                "   Safety Layer",
                justify="center",
            ),
            title="AetherOS Pipeline",
            border_style="cyan",
        )
    )
    console.print(
        Panel(format_status(snapshot), title="System Status", border_style="blue")
    )

    if not decisions:
        console.print(
            Panel(
                Text("System healthy.\nNo recommendations to validate.", style="green"),
                title="Safety Output",
                border_style="green",
            )
        )
        return

    body = Text()
    for index, (rec, result) in enumerate(decisions):
        if index:
            body.append("\n\n")
        body.append_text(format_decision(rec, result))
    console.print(Panel(body, title="Safety Output", border_style="magenta"))
    console.print(f"[dim]Audit log: {audit_path.resolve()}[/dim]")


def run_demo(*, db_path: Path, twice: bool, fixture: bool) -> None:
    """Run the live pipeline once, or twice to demonstrate cooldown.

    Args:
        db_path: SQLite audit database path.
        twice: When True, validate again to show cooldown blocking.
        fixture: When True, inject a synthetic CPU Overload recommendation
            so the demo is visible even on a healthy host.
    """

    telemetry = TelemetryEngine(interval_seconds=1.0)
    telemetry.collect_once()
    system = telemetry.collect_once()
    snapshot = TelemetrySnapshot.from_system_snapshot(system)

    validator = SafetyValidator(
        cooldown=CooldownManager(),
        audit=AuditLogger(db_path),
    )

    if fixture:
        to_check = [
            PolicyRecommendation(
                level="critical",
                title="CPU Overload",
                reason="CPU usage has exceeded 95%.",
                recommended_action="Reduce background workload.",
                confidence=98,
            )
        ]
    else:
        recommendations = PolicyEngine().evaluate_all(snapshot)
        issues = [r for r in recommendations if r.level in ("warning", "critical")]
        to_check = issues if issues else recommendations

    decisions = validator.validate_all(to_check)
    render_pipeline(snapshot, decisions, db_path)

    if twice and to_check:
        console = Console()
        console.print("\n[dim]Second pass (cooldown demo)…[/dim]\n")
        second = validator.validate_all(to_check)
        render_pipeline(snapshot, second, db_path)


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser for the safety demo."""

    parser = argparse.ArgumentParser(
        prog="aetheros-safety",
        description="AetherOS Phase 3 — safety validation (no execution)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/safety_audit.db"),
        help="SQLite audit database path (default: data/safety_audit.db)",
    )
    parser.add_argument(
        "--twice",
        action="store_true",
        help="Run validation twice to demonstrate cooldown blocking",
    )
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="Inject a synthetic CPU Overload recommendation for demo purposes",
    )
    return parser


def main() -> None:
    """CLI entry point for the safety pipeline demo."""

    args = build_parser().parse_args()
    run_demo(db_path=args.db, twice=args.twice, fixture=args.fixture)


if __name__ == "__main__":
    main()
