"""Atlas ProgressBar — horizontal utilization bar (0–100).

Presentation only. Maps percent to green / yellow / red tones.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.progress_bar import ProgressBar
from rich.text import Text


@dataclass(frozen=True, slots=True)
class AtlasProgressBar:
    """Immutable labeled progress bar for CPU / memory / disk style metrics."""

    label: str
    percent: float
    width: int = 24

    def __post_init__(self) -> None:
        if self.width < 4:
            raise ValueError("width must be >= 4")

    def __rich__(self) -> RenderableType:
        pct = max(0.0, min(100.0, float(self.percent)))
        style = _tone(pct)
        bar = ProgressBar(
            total=100,
            completed=pct,
            width=self.width,
            style="grey23",
            complete_style=style,
            finished_style=style,
        )
        return Group(
            Text.assemble((f"{self.label:<8}", "dim"), (f"{pct:5.1f}%", style)),
            bar,
        )


def _tone(percent: float) -> str:
    if percent >= 85.0:
        return "bold red"
    if percent >= 70.0:
        return "bold yellow"
    return "bold green"
