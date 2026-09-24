"""CLI demo for Phase 6 intent engine (read-only)."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros import __version__
from aetheros.decision import DecisionEngine
from aetheros.intent import IntentEngine, IntentStorage
from aetheros.policy_engine import TelemetrySnapshot
from aetheros.safety import AuditLogger, CooldownManager, SafetyValidator


def _demo_snapshot() -> TelemetrySnapshot:
    """Mild healthy snapshot for a predictable intent demo."""

    return TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        cpu_percent=24.0,
        memory_percent=51.0,
        disk_percent=38.0,
        battery_percent=80.0,
        process_count=8,
        top_processes=("code", "python", "chrome"),
    )


def run_demo(*, intent_name: str, intent_db: Path, audit_db: Path) -> None:
    """Print an intent-aware decision summary."""

    intent = IntentEngine(storage=IntentStorage(intent_db), initial=intent_name)
    intent.set_intent(intent_name)
    engine = DecisionEngine(
        intent=intent,
        safety=SafetyValidator(
            cooldown=CooldownManager(),
            audit=AuditLogger(audit_db),
        ),
    )
    report = engine.evaluate_report(_demo_snapshot(), record=False)
    profile = intent.current_intent()

    if report.decision is None or report.decision.severity == "normal":
        title = "System Healthy"
        score = 12 + (profile.latency_weight + profile.efficiency_weight) // 2
        score = max(0, min(100, score))
        action = intent.guidance_text()
        explanation = (
            "No critical resource pressure detected.\n"
            f"Active intent: {profile.name} — {profile.description}"
        )
    else:
        title = report.decision.title
        score = report.decision.priority_score
        action = report.decision.action
        explanation = report.decision.explanation

    console = Console()
    console.print(
        Panel(
            Text(f"AetherOS v{__version__}", style="bold blue", justify="center"),
            border_style="blue",
        )
    )
    info = Table.grid(padding=(0, 2))
    info.add_column(style="bold")
    info.add_column()
    info.add_row("Intent", profile.name)
    info.add_row("Focus", profile.description)
    info.add_row("State", title)
    info.add_row("Decision Score", str(score))
    console.print(Panel(info, title="Intent Summary", border_style="cyan"))
    console.print(
        Panel(
            Text(f"Recommendation:\n{action}\n\n{explanation}"),
            title="Guidance",
            border_style="green",
        )
    )
    console.print("[dim]No system changes performed.[/dim]")


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser for the intent demo."""

    parser = argparse.ArgumentParser(
        prog="aetheros-intent",
        description="AetherOS Phase 6 — intent engine demo (no execution)",
    )
    parser.add_argument(
        "--intent",
        default="Coding",
        help="Intent profile to activate (default: Coding)",
    )
    parser.add_argument(
        "--intent-db",
        type=Path,
        default=Path("data/intent.db"),
        help="SQLite intent database path",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("data/safety_audit.db"),
        help="SQLite audit database path",
    )
    return parser


def main() -> None:
    """CLI entry point for the intent demo."""

    args = build_parser().parse_args()
    run_demo(intent_name=args.intent, intent_db=args.intent_db, audit_db=args.db)


if __name__ == "__main__":
    main()
