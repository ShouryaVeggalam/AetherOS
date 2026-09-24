"""Rich observatory renderer — graphs, timeline, observations.

Presentation only. No recording or event detection here.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aetheros.observatory.models import GraphMetric, SystemEvent

_SPARK = " ▁▂▃▄▅▆▇█"


def sparkline(values: tuple[float, ...] | list[float], width: int = 40) -> str:
    """Render a compact one-line sparkline for 0–100 values."""

    if not values:
        return "·" * width
    series = _resample(list(values), max(8, width))
    chars: list[str] = []
    for value in series:
        idx = int(max(0.0, min(1.0, value / 100.0)) * (len(_SPARK) - 1))
        chars.append(_SPARK[idx])
    return "".join(chars)


def render_ascii_graph(
    values: tuple[float, ...] | list[float],
    *,
    width: int = 42,
    height: int = 4,
    label: str = "CPU",
) -> str:
    """Render a small multi-row ASCII area graph."""

    width = max(8, width)
    height = max(3, height)
    if not values:
        return f"{label}\n" + ("·" * width)
    series = _resample(list(values), width)
    rows = [[" " for _ in range(width)] for _ in range(height)]
    for x, value in enumerate(series):
        level = max(0.0, min(1.0, value / 100.0)) * (height - 1)
        y_top = height - 1 - int(level)
        for y in range(y_top, height):
            rows[y][x] = "█"
    lines = [label] + ["".join(row) for row in rows]
    lines.append(f"now {series[-1]:5.1f}%")
    return "\n".join(lines)


def _resample(values: list[float], width: int) -> list[float]:
    """Resample a series to a fixed width."""

    if len(values) == width:
        return values
    if len(values) == 1:
        return values * width
    if len(values) > width:
        return [
            values[int(round(i * (len(values) - 1) / (width - 1)))]
            for i in range(width)
        ]
    out: list[float] = []
    for i in range(width):
        pos = i * (len(values) - 1) / (width - 1)
        lo = int(pos)
        hi = min(len(values) - 1, lo + 1)
        frac = pos - lo
        out.append(values[lo] * (1 - frac) + values[hi] * frac)
    return out


def _severity_style(severity: str) -> str:
    """Map severity to a Rich style."""

    if severity == "critical":
        return "bold red"
    if severity == "warning":
        return "bold yellow"
    return "cyan"


@dataclass(frozen=True, slots=True)
class ObservatoryPanel:
    """Center observatory panel: sparklines, detail graph, timeline, notes."""

    focus_metric: GraphMetric
    cpu_spark: str
    memory_spark: str
    disk_spark: str
    detail_graph: str
    events: tuple[SystemEvent, ...]
    observations: tuple[str, ...]
    history_offset: int
    sample_count: int
    capacity: int
    window_label: str = "Last 60 Seconds"

    def __rich__(self) -> RenderableType:
        """Assemble the observatory Rich renderable."""

        header = Text.assemble(
            ("Observatory", "bold cyan"),
            ("  ·  ", "dim"),
            (self.window_label, "white"),
            ("  ·  ", "dim"),
            (f"{self.sample_count}/{self.capacity}", "dim"),
            (
                f"  ·  -{self.history_offset}s" if self.history_offset else "  ·  live",
                "yellow" if self.history_offset else "green",
            ),
        )
        sparks = Table.grid(padding=(0, 1))
        sparks.add_column(style="bold", width=8)
        sparks.add_column()
        sparks.add_row("CPU", Text(self.cpu_spark, style="green"))
        sparks.add_row("Memory", Text(self.memory_spark, style="magenta"))
        sparks.add_row("Disk", Text(self.disk_spark, style="cyan"))

        timeline = Table(expand=True, box=None, padding=(0, 1))
        timeline.add_column("Time", style="dim", width=8)
        timeline.add_column("Event", style="bold")
        timeline.add_column("Detail")
        if not self.events:
            timeline.add_row("—", "waiting", "No events yet")
        else:
            for event in self.events:
                timeline.add_row(
                    event.timestamp.strftime("%H:%M:%S"),
                    Text(event.title, style=_severity_style(event.severity)),
                    event.description,
                )

        obs_lines = Text()
        if not self.observations:
            obs_lines.append("No observations yet — collecting history…", style="dim")
        else:
            for note in self.observations:
                obs_lines.append(f"• {note}\n", style="white")

        focus = self.focus_metric.upper()
        body = Group(
            header,
            Text(""),
            sparks,
            Text(""),
            Text(f"Focus ({focus}) — press T to cycle", style="bold"),
            Text(
                self.detail_graph,
                style={
                    "cpu": "green",
                    "memory": "magenta",
                    "disk": "cyan",
                }.get(self.focus_metric, "white"),
            ),
            Text(""),
            Text("Timeline", style="bold"),
            timeline,
            Text(""),
            Text("AI Observations", style="bold"),
            obs_lines,
            Text(""),
            Text(
                "O/ESC leave  ·  ← scroll  ·  T toggle graph  ·  read-only",
                style="dim",
            ),
        )
        return Panel(body, title="Observatory", border_style="cyan")
