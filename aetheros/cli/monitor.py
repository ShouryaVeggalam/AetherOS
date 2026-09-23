"""Live terminal monitor for AetherOS telemetry (Phase 1).

This is a read-only dashboard. It never changes process priority,
kills processes, or writes system config — it only displays data.
"""

from __future__ import annotations

import argparse
from typing import NoReturn

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.telemetry import TelemetryEngine
from aetheros.telemetry.models import SystemSnapshot


def _format_bytes(num_bytes: int) -> str:
    """Convert a byte count into a short human-readable string."""

    units = ("B", "KB", "MB", "GB", "TB")
    value = float(num_bytes)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def render_snapshot(snapshot: SystemSnapshot) -> Group:
    """Build a Rich renderable for one SystemSnapshot."""

    header = Text.assemble(
        ("AetherOS", "bold cyan"),
        ("  ·  telemetry  ·  ", "dim"),
        (snapshot.collected_at.strftime("%Y-%m-%d %H:%M:%S UTC"), "white"),
    )

    cpu = snapshot.cpu
    mem = snapshot.memory

    stats = Table.grid(padding=(0, 2))
    stats.add_column(style="bold")
    stats.add_column()
    stats.add_row("CPU", f"{cpu.percent:5.1f}%")
    stats.add_row(
        "Load",
        f"{cpu.load_avg[0]:.2f} / {cpu.load_avg[1]:.2f} / {cpu.load_avg[2]:.2f}",
    )
    stats.add_row(
        "RAM",
        f"{mem.percent:5.1f}%  ({_format_bytes(mem.used_bytes)} / {_format_bytes(mem.total_bytes)})",
    )
    stats.add_row(
        "Swap",
        f"{mem.swap_percent:5.1f}%  ({_format_bytes(mem.swap_used_bytes)} / {_format_bytes(mem.swap_total_bytes)})",
    )

    if snapshot.battery is not None:
        plugged = "AC" if snapshot.battery.is_plugged_in else "battery"
        stats.add_row("Battery", f"{snapshot.battery.percent:5.1f}%  ({plugged})")
    else:
        stats.add_row("Battery", "n/a")

    disk_table = Table(title="Disks", expand=True)
    disk_table.add_column("Mount")
    disk_table.add_column("Used %", justify="right")
    disk_table.add_column("Used", justify="right")
    disk_table.add_column("Free", justify="right")
    for disk in snapshot.disks:
        disk_table.add_row(
            disk.mountpoint,
            f"{disk.percent:.1f}%",
            _format_bytes(disk.used_bytes),
            _format_bytes(disk.free_bytes),
        )

    proc_table = Table(title="Top processes (by CPU)", expand=True)
    proc_table.add_column("PID", justify="right")
    proc_table.add_column("Name")
    proc_table.add_column("User")
    proc_table.add_column("CPU %", justify="right")
    proc_table.add_column("MEM %", justify="right")
    proc_table.add_column("Status")
    for proc in snapshot.processes:
        proc_table.add_row(
            str(proc.pid),
            proc.name,
            proc.username or "—",
            f"{proc.cpu_percent:.1f}",
            f"{proc.memory_percent:.1f}",
            proc.status,
        )

    return Group(
        Panel(header, border_style="cyan"),
        Panel(stats, title="System", border_style="blue"),
        disk_table,
        proc_table,
    )


def run_monitor(interval_seconds: float = 1.0) -> None:
    """Start the live telemetry dashboard until Ctrl+C."""

    console = Console()
    engine = TelemetryEngine(interval_seconds=interval_seconds)
    # First sample primes process CPU counters; second sample is displayable.
    engine.collect_once()

    with Live(console=console, refresh_per_second=4, screen=False) as live:
        try:
            for snapshot in engine.stream():
                live.update(render_snapshot(snapshot))
        except KeyboardInterrupt:
            console.print("\n[dim]Stopped. Telemetry was read-only — nothing was changed.[/dim]")


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser for the monitor command."""

    parser = argparse.ArgumentParser(
        prog="aetheros-monitor",
        description="AetherOS Phase 1 — live read-only system telemetry",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between samples (default: 1.0)",
    )
    return parser


def main() -> NoReturn | None:
    """CLI entry point for `aetheros-monitor` / `python -m aetheros.cli.monitor`."""

    args = build_parser().parse_args()
    if args.interval <= 0:
        raise SystemExit("--interval must be positive")
    run_monitor(interval_seconds=args.interval)
    return None


if __name__ == "__main__":
    main()
