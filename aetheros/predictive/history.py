"""History adapters for predictive forecasting.

Turns observatory TelemetryPoint windows into numeric series.
Never invents samples. Empty history yields empty series.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from aetheros.observatory.models import TelemetryPoint
from aetheros.predictive.models import MetricName


@dataclass(frozen=True, slots=True)
class MetricSeries:
    """One immutable numeric series with timing metadata.

    Attributes:
        metric: Metric name.
        values: Samples oldest → newest.
        timestamps: Matching timestamps (same length as values).
        sample_interval_seconds: Median gap between samples, or 1.0.
    """

    metric: MetricName
    values: tuple[float, ...]
    timestamps: tuple[datetime, ...]
    sample_interval_seconds: float

    @property
    def window_seconds(self) -> int:
        """Span of the series in seconds."""

        if len(self.timestamps) < 2:
            return 0
        delta = _aware(self.timestamps[-1]) - _aware(self.timestamps[0])
        return max(0, int(delta.total_seconds()))


def series_from_points(
    points: tuple[TelemetryPoint, ...],
    metric: MetricName,
) -> MetricSeries:
    """Extract one metric series from telemetry points."""

    if not points:
        return MetricSeries(metric, (), (), 1.0)
    if metric == "battery":
        paired = [(p.timestamp, p.battery) for p in points if p.battery is not None]
        if not paired:
            return MetricSeries(metric, (), (), 1.0)
        timestamps = tuple(ts for ts, _ in paired)
        values = tuple(float(val) for _, val in paired)
    else:
        timestamps = tuple(p.timestamp for p in points)
        values = tuple(float(_required_metric(p, metric)) for p in points)
    interval = _median_interval(timestamps)
    return MetricSeries(metric, values, timestamps, interval)


def _required_metric(point: TelemetryPoint, metric: MetricName) -> float:
    """Read a non-optional metric from a TelemetryPoint."""

    if metric == "memory":
        return point.memory
    if metric == "disk":
        return point.disk
    return point.cpu


def load_points_from_sqlite(
    db_path: Path,
    *,
    limit: int = 300,
) -> tuple[TelemetryPoint, ...]:
    """Load the newest telemetry_history rows from observatory.db."""

    path = Path(db_path)
    if not path.exists():
        return ()
    query = """
        SELECT timestamp, cpu, memory, disk, battery, intent
        FROM telemetry_history
        ORDER BY id DESC
        LIMIT ?
    """
    with sqlite3.connect(path) as conn:
        rows = conn.execute(query, (limit,)).fetchall()
    points: list[TelemetryPoint] = []
    for stamp, cpu, memory, disk, battery, intent in reversed(rows):
        points.append(
            TelemetryPoint(
                timestamp=_parse_stamp(str(stamp)),
                cpu=float(cpu),
                memory=float(memory),
                disk=float(disk),
                battery=None if battery is None else float(battery),
                intent=str(intent),
            )
        )
    return tuple(points)


def dominant_intent(points: tuple[TelemetryPoint, ...]) -> str | None:
    """Return the most frequent intent label in the window, if any."""

    if not points:
        return None
    counts: dict[str, int] = {}
    for point in points:
        counts[point.intent] = counts.get(point.intent, 0) + 1
    return max(counts, key=counts.get)  # type: ignore[arg-type]


def _median_interval(timestamps: tuple[datetime, ...]) -> float:
    """Median positive gap between consecutive samples."""

    if len(timestamps) < 2:
        return 1.0
    gaps = [
        (_aware(timestamps[i]) - _aware(timestamps[i - 1])).total_seconds()
        for i in range(1, len(timestamps))
    ]
    gaps = [g for g in gaps if g > 0]
    if not gaps:
        return 1.0
    gaps.sort()
    mid = len(gaps) // 2
    if len(gaps) % 2:
        return float(gaps[mid])
    return float((gaps[mid - 1] + gaps[mid]) / 2.0)


def _parse_stamp(value: str) -> datetime:
    """Parse an ISO timestamp into timezone-aware UTC."""

    parsed = datetime.fromisoformat(value)
    return _aware(parsed)


def _aware(value: datetime) -> datetime:
    """Ensure timezone-aware UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
