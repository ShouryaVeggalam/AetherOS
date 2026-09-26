"""Horizon StatCard — compact metric tile for overview and health pages.

Presentation only. Never fetches telemetry or mutates state.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.align import Align
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text


@dataclass(frozen=True, slots=True)
class StatCard:
    """Immutable Rich panel showing a labeled metric value."""

    label: str
    value: str
    subtitle: str = ""
    tone: str = "bright_white"
    border: str = "grey37"

    def __rich__(self) -> RenderableType:
        title = Text(self.label.upper(), style="dim")
        body = Text(self.value, style=f"bold {self.tone}")
        parts: list[RenderableType] = [
            Align.center(title),
            Align.center(body),
        ]
        if self.subtitle:
            parts.append(Align.center(Text(self.subtitle, style="dim")))
        return Panel(
            Group(*parts),
            border_style=self.border,
            padding=(0, 1),
            expand=True,
        )
