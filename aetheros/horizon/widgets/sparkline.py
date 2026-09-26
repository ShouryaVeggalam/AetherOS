"""Horizon Sparkline — compact unicode spark for short numeric series.

Presentation only. Clamps values; never samples live metrics.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from rich.console import RenderableType
from rich.text import Text

_BLOCKS = "▁▂▃▄▅▆▇█"


@dataclass(frozen=True, slots=True)
class HorizonSparkline:
    """Immutable sparkline renderable for a finite numeric series."""

    values: tuple[float, ...]
    label: str = ""
    width: int = 24
    tone: str = "bright_cyan"

    def __post_init__(self) -> None:
        if self.width < 1:
            raise ValueError("width must be >= 1")
        object.__setattr__(self, "values", tuple(self.values))

    def __rich__(self) -> RenderableType:
        spark = render_sparkline(self.values, width=self.width)
        if self.label:
            return Text.assemble((f"{self.label} ", "dim"), (spark, self.tone))
        return Text(spark, style=self.tone)


def render_sparkline(values: Sequence[float], *, width: int = 24) -> str:
    """Map a numeric series to a fixed-width block sparkline string."""

    if width < 1:
        raise ValueError("width must be >= 1")
    if not values:
        return "·" * width
    series = list(values)
    if len(series) > width:
        step = len(series) / width
        series = [series[int(i * step)] for i in range(width)]
    elif len(series) < width:
        series = series + [series[-1]] * (width - len(series))
    lo = min(series)
    hi = max(series)
    span = hi - lo
    if span <= 1e-12:
        return _BLOCKS[0] * width
    out: list[str] = []
    last = len(_BLOCKS) - 1
    for value in series:
        idx = int(round((value - lo) / span * last))
        out.append(_BLOCKS[max(0, min(last, idx))])
    return "".join(out)
