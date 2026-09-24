"""Anomaly detection against trends and near-term forecasts.

Alerts are generated only from measurable deviations in history.
"""

from __future__ import annotations

from aetheros.observatory.models import TelemetryPoint
from aetheros.predictive.history import series_from_points
from aetheros.predictive.models import (
    AnomalyAlert,
    Forecast,
    RiskLevel,
    Trend,
)


def detect_anomalies(
    points: tuple[TelemetryPoint, ...],
    trends: tuple[Trend, ...],
    near_forecast: Forecast | None,
) -> tuple[AnomalyAlert, ...]:
    """Detect unusual metric behavior versus trend and forecast."""

    if len(points) < 3:
        return ()
    alerts: list[AnomalyAlert] = []
    by_metric = {t.metric: t for t in trends}
    alerts.extend(_cpu_jump_alerts(points, by_metric.get("cpu")))
    alerts.extend(_memory_forecast_alerts(points, near_forecast))
    alerts.extend(_disk_growth_alerts(by_metric.get("disk")))
    return tuple(alerts)


def risk_from_anomalies(
    anomalies: tuple[AnomalyAlert, ...],
    stability: int,
) -> RiskLevel:
    """Aggregate anomaly severity and stability into a risk level."""

    if any(a.severity == "high" for a in anomalies) or stability < 35:
        return "high"
    if anomalies or stability < 60:
        return "medium"
    return "low"


def _cpu_jump_alerts(
    points: tuple[TelemetryPoint, ...],
    trend: Trend | None,
) -> list[AnomalyAlert]:
    """Flag CPU jumps far above the linear trend expectation."""

    series = series_from_points(points, "cpu")
    if len(series.values) < 3:
        return []
    expected = _trend_expected(series.values)
    actual = series.values[-1]
    jump = actual - expected
    if jump < 35.0:
        return []
    severity: RiskLevel = "high" if jump >= 45.0 else "medium"
    return [
        AnomalyAlert(
            metric="cpu",
            severity=severity,
            title="CPU Jump",
            description=(
                f"CPU jumped {jump:.0f}% above trend "
                f"(actual {actual:.0f}% vs expected {expected:.0f}%)."
            ),
            deviation=round(jump, 1),
        )
    ]


def _memory_forecast_alerts(
    points: tuple[TelemetryPoint, ...],
    near_forecast: Forecast | None,
) -> list[AnomalyAlert]:
    """Flag memory that already exceeds the near-term forecast."""

    if near_forecast is None or not points:
        return []
    actual = points[-1].memory
    predicted = near_forecast.predicted_memory
    deviation = actual - predicted
    if deviation < 12.0:
        return []
    severity: RiskLevel = "high" if deviation >= 20.0 else "medium"
    return [
        AnomalyAlert(
            metric="memory",
            severity=severity,
            title="Memory Deviation",
            description=(
                f"Memory {actual:.0f}% already exceeds +{near_forecast.horizon}m "
                f"forecast {predicted:.0f}% by {deviation:.0f}%."
            ),
            deviation=round(deviation, 1),
        )
    ]


def _disk_growth_alerts(trend: Trend | None) -> list[AnomalyAlert]:
    """Flag unusually fast disk growth from trend slope."""

    if trend is None or trend.metric != "disk":
        return []
    # Percent points per minute — sustained growth is rare for disk.
    if trend.slope < 0.15:
        return []
    severity: RiskLevel = "high" if trend.slope >= 0.4 else "medium"
    return [
        AnomalyAlert(
            metric="disk",
            severity=severity,
            title="Disk Growth",
            description=(
                f"Disk utilization rising unusually fast "
                f"({trend.slope:+.2f}%/min, σ={trend.volatility:.1f})."
            ),
            deviation=round(trend.slope, 3),
        )
    ]


def _trend_expected(values: tuple[float, ...]) -> float:
    """Expected last value from OLS line through the series."""

    n = len(values)
    xs = list(range(n))
    ys = [float(v) for v in values]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    numer = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return mean_y
    slope = numer / denom
    intercept = mean_y - slope * mean_x
    return intercept + slope * (n - 1)
