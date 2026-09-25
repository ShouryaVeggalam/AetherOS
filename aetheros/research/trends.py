"""Trend engine — directional metric analysis over fixed windows.

Read-only. Returns ``TrendAnalysis`` only when sample evidence exists;
otherwise ``insufficient_data`` with low confidence.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from statistics import mean

from aetheros.observatory.models import TelemetryPoint
from aetheros.research.models import TrendAnalysis, TrendMetric, TrendWindow

_WINDOWS: dict[TrendWindow, timedelta] = {
    "last_hour": timedelta(hours=1),
    "today": timedelta(hours=24),
    "7_days": timedelta(days=7),
    "30_days": timedelta(days=30),
}
_METRICS: tuple[TrendMetric, ...] = (
    "cpu",
    "memory",
    "disk",
    "battery",
    "network",
    "cluster_health",
)
_MIN_SAMPLES = 3
_STABLE_EPS = 2.0


def analyze_trends(
    history: Sequence[TelemetryPoint],
    *,
    now: datetime | None = None,
    windows: Sequence[TrendWindow] | None = None,
    metrics: Sequence[TrendMetric] | None = None,
    network_series: Sequence[float] | None = None,
    cluster_health_series: Sequence[float] | None = None,
) -> tuple[TrendAnalysis, ...]:
    """Compute trends for selected metrics and windows.

    ``network`` and ``cluster_health`` require explicit series evidence;
    without it the trend is ``insufficient_data``.
    """

    stamp = now or datetime.now(UTC)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    selected_windows = tuple(windows) if windows is not None else tuple(_WINDOWS)
    selected_metrics = tuple(metrics) if metrics is not None else _METRICS
    results: list[TrendAnalysis] = []
    for window in selected_windows:
        span = _WINDOWS[window]
        points = _window_points(history, stamp=stamp, span=span)
        for metric in selected_metrics:
            series = _series_for(
                metric,
                points,
                network_series=network_series,
                cluster_health_series=cluster_health_series,
                stamp=stamp,
                span=span,
                history_len=len(history),
            )
            results.append(_trend(metric, window, series))
    return tuple(results)


def _window_points(
    history: Sequence[TelemetryPoint],
    *,
    stamp: datetime,
    span: timedelta,
) -> tuple[TelemetryPoint, ...]:
    start = stamp - span
    selected = []
    for point in history:
        ts = point.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=UTC)
        if start <= ts <= stamp:
            selected.append(point)
    return tuple(selected)


def _series_for(
    metric: TrendMetric,
    points: Sequence[TelemetryPoint],
    *,
    network_series: Sequence[float] | None,
    cluster_health_series: Sequence[float] | None,
    stamp: datetime,
    span: timedelta,
    history_len: int,
) -> tuple[float, ...]:
    if metric == "cpu":
        return tuple(p.cpu for p in points)
    if metric == "memory":
        return tuple(p.memory for p in points)
    if metric == "disk":
        return tuple(p.disk for p in points)
    if metric == "battery":
        return tuple(p.battery for p in points if p.battery is not None)
    if metric == "network":
        if network_series is None:
            return ()
        # Align by taking last N samples matching window density when possible.
        return tuple(float(v) for v in network_series)
    if metric == "cluster_health":
        if cluster_health_series is None:
            return ()
        return tuple(float(v) for v in cluster_health_series)
    return ()


def _trend(
    metric: TrendMetric,
    window: TrendWindow,
    series: Sequence[float],
) -> TrendAnalysis:
    if len(series) < _MIN_SAMPLES:
        return TrendAnalysis(
            metric=metric,
            window=window,
            direction="insufficient_data",
            confidence=max(0.0, min(40.0, 10.0 * len(series))),
        )
    first_half = series[: len(series) // 2]
    second_half = series[len(series) // 2 :]
    delta = mean(second_half) - mean(first_half)
    if abs(delta) < _STABLE_EPS:
        direction: str = "stable"
    elif delta > 0:
        direction = "rising"
    else:
        direction = "falling"
    # Confidence scales with samples and magnitude (capped).
    sample_factor = min(1.0, len(series) / 24.0)
    mag_factor = min(1.0, abs(delta) / 15.0)
    confidence = round(40.0 + 40.0 * sample_factor + 20.0 * mag_factor, 2)
    if direction == "stable":
        confidence = round(50.0 + 30.0 * sample_factor, 2)
    return TrendAnalysis(
        metric=metric,
        window=window,
        direction=direction,  # type: ignore[arg-type]
        confidence=min(100.0, confidence),
    )
