"""AetherOS v1.3 — Predictive Intelligence Engine.

Statistical forecasts from historical telemetry. No ML libraries.
Every prediction includes an explainability payload.
"""

from __future__ import annotations

from aetheros.predictive.anomaly import detect_anomalies, risk_from_anomalies
from aetheros.predictive.confidence import forecast_confidence
from aetheros.predictive.forecasting import (
    ForecastEngine,
    detect_trend,
    exponential_smoothing,
    linear_regression,
    moving_average,
)
from aetheros.predictive.history import (
    MetricSeries,
    dominant_intent,
    load_points_from_sqlite,
    series_from_points,
)
from aetheros.predictive.models import (
    AnomalyAlert,
    Forecast,
    ForecastExplanation,
    PredictiveReport,
    Trend,
)
from aetheros.predictive.renderer import PredictivePanel, format_predictive_report

__all__ = [
    "AnomalyAlert",
    "Forecast",
    "ForecastEngine",
    "ForecastExplanation",
    "MetricSeries",
    "PredictivePanel",
    "PredictiveReport",
    "Trend",
    "detect_anomalies",
    "detect_trend",
    "dominant_intent",
    "exponential_smoothing",
    "forecast_confidence",
    "format_predictive_report",
    "linear_regression",
    "load_points_from_sqlite",
    "moving_average",
    "risk_from_anomalies",
    "series_from_points",
]
