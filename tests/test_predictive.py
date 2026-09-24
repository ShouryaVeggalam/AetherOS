"""Unit tests for AetherOS v1.3 Predictive Intelligence Engine."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from rich.console import Console

from aetheros.observatory.models import TelemetryPoint
from aetheros.observatory.recorder import HistoryRecorder
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.predictive import (
    ForecastEngine,
    detect_trend,
    exponential_smoothing,
    forecast_confidence,
    format_predictive_report,
    linear_regression,
    load_points_from_sqlite,
    moving_average,
    series_from_points,
)


def _points(
    *,
    count: int = 60,
    start_cpu: float = 40.0,
    cpu_step: float = 0.5,
    memory: float = 55.0,
    disk: float = 30.0,
    intent: str = "Coding",
) -> tuple[TelemetryPoint, ...]:
    """Build a rising CPU history window."""

    now = datetime.now(UTC)
    out: list[TelemetryPoint] = []
    for index in range(count):
        stamp = now - timedelta(seconds=count - index)
        cpu = start_cpu + cpu_step * index
        out.append(TelemetryPoint(stamp, cpu, memory, disk, 80.0, intent))
    return tuple(out)


def test_moving_average_and_smoothing() -> None:
    """Statistical helpers should track the series without ML libs."""

    values = (10.0, 20.0, 30.0, 40.0, 50.0)
    assert moving_average(values, window=3) == 40.0
    smoothed = exponential_smoothing(values, alpha=0.5)
    assert 30.0 < smoothed < 50.0


def test_linear_regression_exact() -> None:
    """Manual OLS matches y = x for 0..9."""

    values = tuple(float(i) for i in range(10))
    slope, intercept = linear_regression(values)
    assert abs(slope - 1.0) < 1e-9
    assert abs(intercept - 0.0) < 1e-9


def test_detect_rising_trend() -> None:
    """Steadily rising CPU should classify as rising."""

    points = _points(count=40, start_cpu=20.0, cpu_step=1.0)
    series = series_from_points(points, "cpu")
    trend = detect_trend(series)
    assert trend.metric == "cpu"
    assert trend.direction == "rising"
    assert trend.slope > 0


def test_predict_horizons_and_explanation() -> None:
    """Engine should emit 5/15/60 forecasts with explainability."""

    engine = ForecastEngine()
    report = engine.predict(_points(count=90, start_cpu=35.0, cpu_step=0.4))
    horizons = {f.horizon for f in report.forecasts}
    assert horizons == {5, 15, 60}
    assert report.explanation.window_samples == 90
    assert "linear regression" in report.explanation.method
    assert report.explanation.reason
    assert 0 <= report.expected_stability <= 100
    f5 = engine.predict_5_min(_points(count=40))
    f15 = engine.predict_15_min(_points(count=40))
    f60 = engine.predict_60_min(_points(count=40))
    assert f5.horizon == 5 and f15.horizon == 15 and f60.horizon == 60
    # Longer horizon should not increase confidence on same data.
    assert f60.confidence <= f5.confidence


def test_confidence_penalizes_short_history() -> None:
    """Few samples and long horizons should lower confidence."""

    short = forecast_confidence(sample_count=5, horizon=60, volatility=20.0)
    long = forecast_confidence(sample_count=250, horizon=5, volatility=2.0)
    assert short < long
    assert forecast_confidence(sample_count=0, horizon=5, volatility=0.0) == 0


def test_anomaly_cpu_jump() -> None:
    """A sudden CPU spike above trend should raise an alert."""

    now = datetime.now(UTC)
    points = [
        TelemetryPoint(
            now - timedelta(seconds=10 - i), 40.0, 50.0, 20.0, 80.0, "Coding"
        )
        for i in range(9)
    ]
    points.append(TelemetryPoint(now, 95.0, 50.0, 20.0, 80.0, "Coding"))
    engine = ForecastEngine()
    report = engine.predict(tuple(points))
    cpu_alerts = [a for a in report.anomalies if a.metric == "cpu"]
    assert cpu_alerts
    assert "jumped" in cpu_alerts[0].description.lower()


def test_sqlite_history_roundtrip(tmp_path: Path) -> None:
    """Forecast engine can load points persisted by HistoryRecorder."""

    db = tmp_path / "observatory.db"
    recorder = HistoryRecorder(db_path=db, capacity=300)
    base = datetime.now(UTC)
    for index in range(25):
        snap = TelemetrySnapshot(
            timestamp=base + timedelta(seconds=index),
            cpu_percent=30.0 + index,
            memory_percent=50.0,
            disk_percent=20.0,
            battery_percent=90.0,
            process_count=1,
            top_processes=("a",),
        )
        recorder.record_telemetry(snap, "Coding")
    loaded = load_points_from_sqlite(db, limit=300)
    assert len(loaded) == 25
    report = ForecastEngine().predict(loaded)
    assert report.forecasts
    assert report.now_cpu == loaded[-1].cpu


def test_renderer_panel() -> None:
    """Rich panel should include horizons, confidence, and reason."""

    report = ForecastEngine().predict(_points(count=50))
    panel = format_predictive_report(report)
    console = Console(record=True, width=100)
    console.print(panel)
    text = console.export_text()
    assert "PREDICTIVE INTELLIGENCE" in text
    assert "+5m" in text
    assert "Confidence" in text
    assert "Risk" in text
