"""Horizon Observatory app — Rich Live loop for global infrastructure views.

Presentation layer only. Consumes ``HorizonSnapshot``; never mutates engines.
Does not change telemetry, reasoning, Digital Twin, scheduler, or consensus.
"""

from __future__ import annotations

import argparse
import select
import sys
import termios
import time
import tty
from dataclasses import dataclass

from rich.console import Console
from rich.live import Live

from aetheros.horizon.demo import build_demo_snapshot
from aetheros.horizon.router import PAGE_IDS, HorizonRouter, PageId
from aetheros.horizon.snapshot import HorizonSnapshot


@dataclass
class HorizonAppState:
    """Mutable UI navigation state (presentation only)."""

    page: PageId = "overview"
    snapshot: HorizonSnapshot | None = None


def poll_key(timeout: float = 0.05) -> str | None:
    """Non-blocking single-key read."""

    if not sys.stdin.isatty():
        time.sleep(timeout)
        return None
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if not ready:
        return None
    char = sys.stdin.read(1)
    if char == "\x1b":
        return "ESC"
    return char


def render_app(
    state: HorizonAppState,
    *,
    router: HorizonRouter | None = None,
) -> object:
    """Build the current Horizon frame for Live display."""

    active = router or HorizonRouter.default()
    snap = state.snapshot or HorizonSnapshot()
    return active.render(state.page, snap, with_chrome=True)


def handle_key(state: HorizonAppState, key: str, router: HorizonRouter) -> bool:
    """Apply a keypress. Return False when the app should quit."""

    if not key:
        return True
    lowered = key.lower() if len(key) == 1 else key
    if lowered in {"q", "ESC", "\x1b"}:
        return False
    page = router.resolve_key(lowered)
    if page is not None:
        state.page = page
    return True


def run(
    *,
    snapshot: HorizonSnapshot | None = None,
    demo: bool = True,
    refresh: float = 8.0,
) -> int:
    """Run the Horizon Live loop. Returns process exit code."""

    router = HorizonRouter.default()
    snap = snapshot
    if snap is None and demo:
        snap = build_demo_snapshot()
    state = HorizonAppState(page="overview", snapshot=snap or HorizonSnapshot())
    console = Console()

    if not sys.stdin.isatty():
        console.print(render_app(state, router=router))
        return 0

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        with Live(
            render_app(state, router=router),
            console=console,
            refresh_per_second=refresh,
            screen=True,
        ) as live:
            while True:
                key = poll_key(0.1)
                if key is not None:
                    if not handle_key(state, key, router):
                        break
                    live.update(render_app(state, router=router))
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry for ``aetheros-horizon``."""

    parser = argparse.ArgumentParser(description="AetherOS Horizon Observatory")
    parser.add_argument(
        "--page",
        default="overview",
        choices=list(PAGE_IDS),
        help="Initial page (non-interactive prints this page)",
    )
    parser.add_argument(
        "--no-demo",
        action="store_true",
        help="Start with an empty snapshot instead of demo data",
    )
    args = parser.parse_args(argv)
    snap = None if args.no_demo else build_demo_snapshot()
    state = HorizonAppState(page=args.page, snapshot=snap)  # type: ignore[arg-type]
    if not sys.stdin.isatty():
        Console().print(render_app(state))
        return 0
    return run(snapshot=snap, demo=not args.no_demo)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
