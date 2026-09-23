"""CLI demo for Phase 4 decision engine (advice only, never executes)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.decision import DecisionEngine, DecisionReport
from aetheros.policy_engine import PolicyEngine, TelemetrySnapshot
from aetheros.safety import AuditLogger, CooldownManager, SafetyValidator
from aetheros.telemetry import TelemetryEngine


def _status_notes(snapshot: TelemetrySnapshot) -> list[str]:
    """Build healthy-resource labels for the demo display."""

    notes: list[str] = []
    if snapshot.memory_percent < 90.0:
        notes.append("Memory Healthy")
    if snapshot.disk_percent < 90.0:
        notes.append("Disk Healthy")
    return notes


def render_report(report: DecisionReport) -> None:
    """Print the Phase-4 decision engine demo layout."""

    console = Console()
    snapshot = report.snapshot

    console.print(
        Panel(
            Text("AetherOS Decision Engine", style="bold cyan", justify="center"),
            border_style="cyan",
        )
    )

    status = Table.grid(padding=(0, 2))
    status.add_column(style="bold")
    status.add_column()
    status.add_row("CPU", f"{snapshot.cpu_percent:.0f}%")
    status.add_row("Memory", f"{snapshot.memory_percent:.0f}%")
    status.add_row("Disk", f"{snapshot.disk_percent:.0f}%")
    console.print(Panel(status, title="System State", border_style="blue"))

    approved_lines = Text()
    if report.approved:
        for rec in report.approved:
            approved_lines.append(f"{rec.title}\n", style="green")
    for note in _status_notes(snapshot):
        approved_lines.append(f"{note}\n", style="dim cyan")
    if not report.approved and not _status_notes(snapshot):
        approved_lines.append("None", style="dim")
    console.print(
        Panel(approved_lines, title="Approved Recommendations", border_style="green")
    )

    if report.decision is None:
        console.print(
            Panel(
                Text("No decision.\nSystem healthy or all advice was blocked.", style="dim"),
                title="Final Decision",
                border_style="yellow",
            )
        )
        return

    decision = report.decision
    body = Text()
    body.append(f"PRIORITY SCORE: {decision.priority_score}\n\n", style="bold magenta")
    body.append(f"Action: {decision.action}\n\n")
    body.append("Explanation:\n", style="bold")
    body.append(decision.explanation)
    console.print(Panel(body, title="Final Decision", border_style="magenta"))


def _fixture_snapshot() -> TelemetrySnapshot:
    """Synthetic overloaded snapshot for a predictable demo."""

    return TelemetrySnapshot(
        timestamp=datetime.now(timezone.utc),
        cpu_percent=97.0,
        memory_percent=68.0,
        disk_percent=40.0,
        battery_percent=None,
        process_count=12,
        top_processes=("chrome", "python", "node"),
    )


def _fixture_engine(db_path: Path) -> DecisionEngine:
    """Build a DecisionEngine with a fixture-friendly policy path.

    Uses the real PolicyEngine against a hot CPU snapshot so CPU Overload
    is produced naturally, then safety + scoring pick the winner.
    """

    return DecisionEngine(
        policy=PolicyEngine(),
        safety=SafetyValidator(
            cooldown=CooldownManager(),
            audit=AuditLogger(db_path),
        ),
    )


def run_demo(*, db_path: Path, fixture: bool) -> None:
    """Collect (or synthesize) telemetry and print a decision report."""

    if fixture:
        snapshot = _fixture_snapshot()
        engine = _fixture_engine(db_path)
        report = engine.evaluate_report(snapshot)
        render_report(report)
        return

    telemetry = TelemetryEngine(interval_seconds=1.0)
    telemetry.collect_once()
    system = telemetry.collect_once()
    snapshot = TelemetrySnapshot.from_system_snapshot(system)
    engine = DecisionEngine(
        safety=SafetyValidator(
            cooldown=CooldownManager(),
            audit=AuditLogger(db_path),
        )
    )
    render_report(engine.evaluate_report(snapshot))


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser for the decision demo."""

    parser = argparse.ArgumentParser(
        prog="aetheros-decision",
        description="AetherOS Phase 4 — decision engine (no execution)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/safety_audit.db"),
        help="SQLite audit database path",
    )
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="Use a synthetic CPU=97%%/Memory=68%% snapshot for a stable demo",
    )
    return parser


def main() -> None:
    """CLI entry point for the decision engine demo."""

    args = build_parser().parse_args()
    run_demo(db_path=args.db, fixture=args.fixture)


if __name__ == "__main__":
    main()
