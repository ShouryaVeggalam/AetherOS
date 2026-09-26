"""Atlas layout — header / footer chrome around a page body.

Presentation shell only. Does not own navigation state.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

NAV_HINT = (
    "O Overview · F Federation · T Topology · S Scheduler · "
    "G Consensus · D Twin · R Research · H Health · Q Quit"
)


def render_header(*, page: str, subtitle: str = "Distributed Observatory") -> Panel:
    """Top chrome with Atlas brand and active page name."""

    body = Text.assemble(
        ("ATLAS", "bold bright_white"),
        ("  ", ""),
        (subtitle, "dim"),
        ("\n", ""),
        (f"Page  {page}", "bright_cyan"),
    )
    return Panel(body, border_style="grey37", padding=(0, 1))


def render_footer(*, page: str) -> Panel:
    """Bottom chrome with navigation hints."""

    body = Text.assemble(
        (NAV_HINT, "dim"),
        ("\n", ""),
        (f"Active · {page}  ·  Read-only", "dim"),
    )
    return Panel(body, border_style="grey37", padding=(0, 1))


def compose_frame(
    page_body: RenderableType,
    *,
    page: str,
) -> RenderableType:
    """Stack header + page body + footer into one renderable."""

    return Group(
        render_header(page=page),
        page_body,
        render_footer(page=page),
    )
