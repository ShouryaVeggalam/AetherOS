"""CLI demo for Phase 9 autonomous research (read-only)."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from aetheros.intent import IntentEngine, IntentStorage
from aetheros.learning import LearningEngine
from aetheros.policy_engine import TelemetrySnapshot
from aetheros.research import ResearchEngine
from aetheros.safety import AuditLogger


def _snapshot_from_args(cpu: float, memory: float, disk: float) -> TelemetrySnapshot:
    """Build a TelemetrySnapshot for the demo."""

    return TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=disk,
        battery_percent=None,
        process_count=10,
        top_processes=("code", "chrome", "python"),
    )


def run_demo(
    *,
    intent_name: str,
    intent_db: Path,
    audit_db: Path,
    reports_dir: Path,
    cpu: float,
    memory: float,
) -> None:
    """Run autonomous research and print a Rich summary."""

    console = Console()
    console.print(
        Panel(Text("Autonomous Research", style="bold cyan"), border_style="cyan")
    )
    console.print("[dim]Generating Strategies...[/dim]")

    intent = IntentEngine(storage=IntentStorage(intent_db), initial=intent_name)
    intent.set_intent(intent_name)
    engine = ResearchEngine(
        learning=LearningEngine(audit=AuditLogger(audit_db)),
        reports_dir=reports_dir,
    )
    report = engine.run(
        _snapshot_from_args(cpu, memory, 40.0),
        intent.current_intent(),
        write_report=True,
    )

    console.print(f"[green]{len(report.candidates)} strategies created.[/green]")
    console.print("[green]Simulation complete.[/green]\n")

    if report.winner is None:
        console.print("[yellow]No winner produced.[/yellow]")
        return

    winner = report.winner
    cpu_delta = winner.strategy.expected_cpu_delta
    improvement = abs(cpu_delta) if cpu_delta < 0 else cpu_delta
    body = Text()
    body.append("Winner\n", style="bold magenta")
    body.append(f"{winner.strategy.title}\n\n", style="bold white")
    body.append(f"Overall Score: {winner.rank_score:.0f}\n")
    body.append(f"Estimated CPU Improvement: +{improvement:.0f}%\n\n")
    body.append("Reason:\n", style="bold")
    body.append(f"{winner.reason}\n")
    console.print(Panel(body, title="Research Result", border_style="magenta"))
    console.print(f"[dim]Report saved successfully: {report.report_path}[/dim]")
    console.print("[dim]No system changes performed.[/dim]")


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the research demo."""

    parser = argparse.ArgumentParser(
        prog="aetheros-research",
        description="AetherOS Phase 9 — autonomous research (simulation only)",
    )
    parser.add_argument("--intent", default="Coding", help="Intent profile name")
    parser.add_argument("--intent-db", type=Path, default=Path("data/intent.db"))
    parser.add_argument("--db", type=Path, default=Path("data/safety_audit.db"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    parser.add_argument("--cpu", type=float, default=72.0)
    parser.add_argument("--memory", type=float, default=58.0)
    return parser


def main() -> None:
    """CLI entry point for autonomous research."""

    args = build_parser().parse_args()
    run_demo(
        intent_name=args.intent,
        intent_db=args.intent_db,
        audit_db=args.db,
        reports_dir=args.reports_dir,
        cpu=args.cpu,
        memory=args.memory,
    )


if __name__ == "__main__":
    main()
