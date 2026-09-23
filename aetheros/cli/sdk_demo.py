"""CLI demo for Phase 10 Kernel Intelligence SDK."""

from __future__ import annotations

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.core import AetherCore
from aetheros.sdk import PluginRegistry


def run_demo(*, state_path: Path) -> None:
    """Load plugins and print a Developer Console style summary."""

    plugins_root = Path(__file__).resolve().parents[1] / "plugins"
    core = AetherCore()
    core.registry = PluginRegistry(
        plugin_dirs=(plugins_root,),
        state_path=state_path,
    )
    core.bootstrap()
    records = core.registry.list_plugins()
    summary = core.registry.safety_summary()

    console = Console()
    console.print(
        Panel(Text("Developer Console", style="bold blue", justify="center"), border_style="blue")
    )
    table = Table(title="Installed Plugins", expand=True)
    table.add_column("Plugin")
    table.add_column("Version")
    table.add_column("Status")
    table.add_column("Author")
    table.add_column("Safety")
    for record in records:
        if not record.verified:
            status, safety = "Rejected", "Unsafe"
        elif record.enabled:
            status, safety = "Enabled", "Verified"
        else:
            status, safety = "Disabled", "Verified"
        table.add_row(record.name, record.version, status, record.author, safety)
    console.print(table)
    console.print(
        Panel(
            Text(
                f"{summary['verified']} Verified\n{summary['unsafe']} Unsafe",
                justify="left",
            ),
            title="Safety",
            border_style="green" if summary["unsafe"] == 0 else "red",
        )
    )
    console.print("[dim]Plugins cannot execute shell commands or modify the kernel.[/dim]")


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the SDK demo."""

    parser = argparse.ArgumentParser(
        prog="aetheros-sdk",
        description="AetherOS Phase 10 — Kernel Intelligence SDK demo",
    )
    parser.add_argument(
        "--state",
        type=Path,
        default=Path("data/plugin_state.json"),
        help="Plugin enable/disable state file",
    )
    return parser


def main() -> None:
    """CLI entry point for the SDK demo."""

    args = build_parser().parse_args()
    run_demo(state_path=args.state)


if __name__ == "__main__":
    main()
