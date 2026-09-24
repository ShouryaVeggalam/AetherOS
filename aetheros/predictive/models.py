"""Predictive Intelligence data contracts for AetherOS v1.3.

Immutable forecasts and trends. Statistical only — no ML libraries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

HorizonMinutes = Literal[5, 15, 60]
TrendDirection = Literal["rising", "stable", "falling", "volatile"]
RiskLevel = Literal["low", "medium", "high"]
MetricName = Literal["cpu", "memory", "disk", "battery"]


@dataclass(frozen=True, slots=True)
class Forecast:
    """One immutable multi-metric forecast for a time horizon.

    Attributes:
        horizon: Forecast horizon in minutes (5, 15, or 60).
        predicted_cpu: Forecast CPU percent 0–100.
        predicted_memory: Forecast memory percent 0–100.
        predicted_disk: Forecast disk percent 0–100.
        predicted_battery: Forecast battery percent, or None if unknown.
        confidence: Forecast confidence 0–100.
    """

    horizon: HorizonMinutes
    predicted_cpu: float
    predicted_memory: float
    predicted_disk: float
    predicted_battery: float | None
    confidence: int

    def __post_init__(self) -> None:
        """Validate confidence and horizon bounds."""

        if self.horizon not in (5, 15, 60):
            raise ValueError("horizon must be 5, 15, or 60")
        if not 0 <= self.confidence <= 100:
            raise ValueError("confidence must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class Trend:
    """Trend classification for one metric series.

    Attributes:
        metric: Metric name (cpu, memory, disk, battery).
        direction: rising, stable, falling, or volatile.
        slope: Units per minute from linear regression.
        volatility: Sample standard deviation of the series.
    """

    metric: MetricName
    direction: TrendDirection
    slope: float
    volatility: float


@dataclass(frozen=True, slots=True)
class AnomalyAlert:
    """One anomaly detected against trend or forecast.

    Attributes:
        metric: Metric that triggered the alert.
        severity: low, medium, or high risk contribution.
        title: Short alert label.
        description: Traceable explanation of the deviation.
        deviation: Magnitude of the anomaly (percent points).
    """

    metric: MetricName
    severity: RiskLevel
    title: str
    description: str
    deviation: float


@dataclass(frozen=True, slots=True)
class ForecastExplanation:
    """Explainability payload for a predictive report.

    Attributes:
        window_samples: Number of history samples used.
        window_seconds: Span of the history window in seconds.
        method: Forecasting methods applied (plain text).
        slope_summary: Per-metric slope statements.
        volatility_summary: Per-metric volatility statements.
        confidence_summary: How confidence was derived.
        reason: Human-readable overall reason grounded in data.
    """

    window_samples: int
    window_seconds: int
    method: str
    slope_summary: tuple[str, ...]
    volatility_summary: tuple[str, ...]
    confidence_summary: str
    reason: str


@dataclass(frozen=True, slots=True)
class PredictiveReport:
    """Full predictive intelligence output for the dashboard.

    Attributes:
        now_cpu: Current CPU percent.
        now_memory: Current memory percent.
        now_disk: Current disk percent.
        now_battery: Current battery percent, or None.
        forecasts: Forecasts for 5, 15, and 60 minutes.
        trends: Trend objects per metric.
        anomalies: Detected anomaly alerts.
        expected_stability: 0–100 stability score.
        risk: Aggregate risk level.
        explanation: Traceable forecast explanation.
    """

    now_cpu: float
    now_memory: float
    now_disk: float
    now_battery: float | None
    forecasts: tuple[Forecast, ...]
    trends: tuple[Trend, ...]
    anomalies: tuple[AnomalyAlert, ...]
    expected_stability: int
    risk: RiskLevel
    explanation: ForecastExplanation
