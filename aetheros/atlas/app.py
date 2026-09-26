"""Atlas Dashboard app — Rich Live loop for the distributed observatory.

Presentation layer only. Consumes ``AtlasSnapshot``; never mutates engines.
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

from aetheros.atlas.demo import build_demo_snapshot
from aetheros.atlas.router import PAGE_IDS, AtlasRouter, PageId
from aetheros.atlas.snapshot import AtlasSnapshot


@dataclass
class AtlasAppState:
    """Mutable UI navigation state (presentation only)."""

    page: PageId = "overview"
    snapshot: AtlasSnapshot | None = None


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
    state: AtlasAppState,
    *,
    router: AtlasRouter | None = None,
) -> object:
    """Build the current Atlas frame for Live display."""

    active = router or AtlasRouter.default()
    snap = state.snapshot or AtlasSnapshot()
    return active.render(state.page, snap, with_chrome=True)


def handle_key(state: AtlasAppState, key: str, router: AtlasRouter) -> bool:
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
    snapshot: AtlasSnapshot | None = None,
    demo: bool = True,
    refresh: float = 8.0,
) -> int:
    """Run the Atlas Live loop. Returns process exit code."""

    router = AtlasRouter.default()
    snap = snapshot
    if snap is None and demo:
        snap = build_demo_snapshot()
    state = AtlasAppState(page="overview", snapshot=snap or AtlasSnapshot())
    console = Console()

    if not sys.stdin.isatty():
        # Non-interactive: print overview once and exit.
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
    """CLI entry for ``aetheros-atlas``."""

    parser = argparse.ArgumentParser(description="AetherOS Atlas Dashboard")
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
    state = AtlasAppState(page=args.page, snapshot=snap)  # type: ignore[arg-type]
    if not sys.stdin.isatty():
        Console().print(render_app(state))
        return 0
    return run(snapshot=snap, demo=not args.no_demo)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
