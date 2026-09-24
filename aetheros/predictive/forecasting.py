"""Forecast engine — statistical prediction without ML libraries.

Implements moving averages, exponential smoothing, and manual
ordinary least-squares linear regression. No NumPy / pandas / sklearn.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.observatory.models import TelemetryPoint
from aetheros.predictive.anomaly import detect_anomalies, risk_from_anomalies
from aetheros.predictive.confidence import forecast_confidence
from aetheros.predictive.history import (
    MetricSeries,
    dominant_intent,
    series_from_points,
)
from aetheros.predictive.models import (
    Forecast,
    ForecastExplanation,
    HorizonMinutes,
    MetricName,
    PredictiveReport,
    Trend,
    TrendDirection,
)


@dataclass
class ForecastEngine:
    """Predict future resource usage from historical telemetry points."""

    def predict(
        self,
        points: tuple[TelemetryPoint, ...],
    ) -> PredictiveReport:
        """Build a full predictive report from history points."""

        cpu = series_from_points(points, "cpu")
        memory = series_from_points(points, "memory")
        disk = series_from_points(points, "disk")
        battery = series_from_points(points, "battery")
        trends = (
            detect_trend(cpu),
            detect_trend(memory),
            detect_trend(disk),
            detect_trend(battery),
        )
        forecasts = (
            self.predict_5_min(points),
            self.predict_15_min(points),
            self.predict_60_min(points),
        )
        anomalies = detect_anomalies(points, trends, forecasts[0])
        stability = expected_stability(forecasts, trends, anomalies)
        risk = risk_from_anomalies(anomalies, stability)
        explanation = explain_forecast(points, trends, forecasts)
        now = points[-1] if points else None
        return PredictiveReport(
            now_cpu=now.cpu if now else 0.0,
            now_memory=now.memory if now else 0.0,
            now_disk=now.disk if now else 0.0,
            now_battery=now.battery if now else None,
            forecasts=forecasts,
            trends=trends,
            anomalies=anomalies,
            expected_stability=stability,
            risk=risk,
            explanation=explanation,
        )

    def predict_5_min(self, points: tuple[TelemetryPoint, ...]) -> Forecast:
        """Forecast resource usage five minutes ahead."""

        return self._predict_horizon(points, 5)

    def predict_15_min(self, points: tuple[TelemetryPoint, ...]) -> Forecast:
        """Forecast resource usage fifteen minutes ahead."""

        return self._predict_horizon(points, 15)

    def predict_60_min(self, points: tuple[TelemetryPoint, ...]) -> Forecast:
        """Forecast resource usage sixty minutes ahead."""

        return self._predict_horizon(points, 60)

    def _predict_horizon(
        self,
        points: tuple[TelemetryPoint, ...],
        horizon: HorizonMinutes,
    ) -> Forecast:
        """Blend MA + ES + linear regression for one horizon."""

        cpu_s = series_from_points(points, "cpu")
        mem_s = series_from_points(points, "memory")
        disk_s = series_from_points(points, "disk")
        batt_s = series_from_points(points, "battery")
        cpu = _blend_forecast(cpu_s, horizon)
        memory = _blend_forecast(mem_s, horizon)
        disk = _blend_forecast(disk_s, horizon)
        battery = _blend_forecast(batt_s, horizon) if batt_s.values else None
        conf = forecast_confidence(
            sample_count=len(points),
            horizon=horizon,
            volatility=_mean_volatility((cpu_s, mem_s, disk_s)),
        )
        return Forecast(
            horizon=horizon,
            predicted_cpu=_clamp(cpu),
            predicted_memory=_clamp(memory),
            predicted_disk=_clamp(disk),
            predicted_battery=None if battery is None else _clamp(battery),
            confidence=conf,
        )


def moving_average(values: tuple[float, ...] | list[float], window: int = 5) -> float:
    """Simple moving average of the last `window` samples."""

    if not values:
        return 0.0
    width = max(1, min(window, len(values)))
    chunk = list(values)[-width:]
    return sum(chunk) / len(chunk)


def exponential_smoothing(
    values: tuple[float, ...] | list[float],
    alpha: float = 0.3,
) -> float:
    """Single-parameter exponential smoothing; returns the last level."""

    if not values:
        return 0.0
    alpha = max(0.01, min(0.99, alpha))
    level = float(values[0])
    for value in values[1:]:
        level = alpha * float(value) + (1.0 - alpha) * level
    return level


def linear_regression(
    values: tuple[float, ...] | list[float],
) -> tuple[float, float]:
    """Manual OLS slope/intercept for y against index x = 0..n-1.

    Returns:
        (slope_per_sample, intercept). Slope is 0 when n < 2.
    """

    n = len(values)
    if n == 0:
        return 0.0, 0.0
    if n == 1:
        return 0.0, float(values[0])
    xs = list(range(n))
    ys = [float(v) for v in values]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    numer = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return 0.0, mean_y
    slope = numer / denom
    intercept = mean_y - slope * mean_x
    return slope, intercept


def predict_value(
    series: MetricSeries,
    horizon_minutes: int,
) -> float:
    """Project one series forward using blended statistical methods."""

    return _blend_forecast(series, horizon_minutes)


def detect_trend(series: MetricSeries) -> Trend:
    """Classify a metric series as rising, stable, falling, or volatile."""

    metric: MetricName = series.metric
    if len(series.values) < 2:
        return Trend(metric=metric, direction="stable", slope=0.0, volatility=0.0)
    slope_per_sample, _ = linear_regression(series.values)
    interval = max(series.sample_interval_seconds, 0.001)
    slope_per_minute = slope_per_sample * (60.0 / interval)
    volatility = sample_std(series.values)
    direction = _classify_direction(slope_per_minute, volatility)
    return Trend(
        metric=metric,
        direction=direction,
        slope=round(slope_per_minute, 4),
        volatility=round(volatility, 4),
    )


def sample_std(values: tuple[float, ...] | list[float]) -> float:
    """Population-safe sample standard deviation (n-1)."""

    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    var = sum((float(v) - mean) ** 2 for v in values) / (n - 1)
    return var**0.5


def expected_stability(
    forecasts: tuple[Forecast, ...],
    trends: tuple[Trend, ...],
    anomalies: tuple,
) -> int:
    """Estimate 0–100 expected stability from forecasts and trends."""

    if not forecasts:
        return 50
    near = forecasts[0]
    pressure = (
        near.predicted_cpu * 0.45
        + near.predicted_memory * 0.35
        + near.predicted_disk * 0.20
    )
    base = 100.0 - pressure * 0.7
    volatile = sum(1 for t in trends if t.direction == "volatile")
    base -= volatile * 8.0
    base -= len(anomalies) * 6.0
    rising_cpu = any(t.metric == "cpu" and t.direction == "rising" for t in trends)
    if rising_cpu and near.predicted_cpu > 80:
        base -= 10.0
    return int(max(0, min(100, round(base))))


def explain_forecast(
    points: tuple[TelemetryPoint, ...],
    trends: tuple[Trend, ...],
    forecasts: tuple[Forecast, ...],
) -> ForecastExplanation:
    """Build a traceable explanation for the predictive report."""

    window_seconds = 0
    if len(points) >= 2:
        delta = points[-1].timestamp - points[0].timestamp
        window_seconds = max(0, int(delta.total_seconds()))
    slopes = tuple(
        f"{t.metric}: slope {t.slope:+.3f}%/min ({t.direction})" for t in trends
    )
    vols = tuple(f"{t.metric}: σ={t.volatility:.2f}" for t in trends)
    avg_conf = (
        int(round(sum(f.confidence for f in forecasts) / len(forecasts)))
        if forecasts
        else 0
    )
    conf_text = (
        f"Confidence averages {avg_conf}% from sample_count={len(points)}, "
        f"horizon penalty, and mean volatility."
    )
    intent = dominant_intent(points)
    cpu_trend = next((t for t in trends if t.metric == "cpu"), None)
    reason = _reason_text(intent, cpu_trend, len(points), window_seconds)
    return ForecastExplanation(
        window_samples=len(points),
        window_seconds=window_seconds,
        method="moving average + exponential smoothing + linear regression",
        slope_summary=slopes,
        volatility_summary=vols,
        confidence_summary=conf_text,
        reason=reason,
    )


def _blend_forecast(series: MetricSeries, horizon_minutes: int) -> float:
    """Blend MA, ES, and linear projection for one horizon."""

    if not series.values:
        return 0.0
    ma = moving_average(series.values, window=min(12, len(series.values)))
    es = exponential_smoothing(series.values, alpha=0.35)
    slope, intercept = linear_regression(series.values)
    steps = _steps_ahead(series, horizon_minutes)
    linear = intercept + slope * (len(series.values) - 1 + steps)
    # Near-term favors ES; longer horizons favor linear trend + MA anchor.
    if horizon_minutes <= 5:
        blended = 0.25 * ma + 0.45 * es + 0.30 * linear
    elif horizon_minutes <= 15:
        blended = 0.30 * ma + 0.30 * es + 0.40 * linear
    else:
        blended = 0.35 * ma + 0.20 * es + 0.45 * linear
    return blended


def _steps_ahead(series: MetricSeries, horizon_minutes: int) -> float:
    """Convert horizon minutes into sample steps using median interval."""

    interval = max(series.sample_interval_seconds, 0.001)
    return (horizon_minutes * 60.0) / interval


def _classify_direction(slope_per_minute: float, volatility: float) -> TrendDirection:
    """Map slope and volatility into a trend label."""

    if volatility >= 12.0:
        return "volatile"
    if slope_per_minute >= 0.35:
        return "rising"
    if slope_per_minute <= -0.35:
        return "falling"
    return "stable"


def _mean_volatility(series_list: tuple[MetricSeries, ...]) -> float:
    """Average volatility across non-empty series."""

    vols = [sample_std(s.values) for s in series_list if s.values]
    if not vols:
        return 0.0
    return sum(vols) / len(vols)


def _reason_text(
    intent: str | None,
    cpu_trend: Trend | None,
    samples: int,
    window_seconds: int,
) -> str:
    """Compose a grounded reason string from available history facts."""

    minutes = max(1, window_seconds // 60) if window_seconds else 0
    parts: list[str] = []
    if intent:
        parts.append(f"{intent} intent dominates the last {samples} samples")
    if cpu_trend is not None:
        parts.append(
            f"CPU trend is {cpu_trend.direction} "
            f"({cpu_trend.slope:+.2f}%/min, σ={cpu_trend.volatility:.1f})"
        )
    if minutes:
        parts.append(f"history window spans ~{minutes} minute(s)")
    if not parts:
        return "Insufficient history for a detailed forecast reason."
    return "; ".join(parts) + "."


def _clamp(value: float) -> float:
    """Clamp a percent forecast into [0, 100]."""

    return max(0.0, min(100.0, round(value, 1)))
