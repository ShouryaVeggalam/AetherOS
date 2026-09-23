"""Unit tests for Phase 2 policy rules and engine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from aetheros.policy_engine import PolicyEngine, PolicyRecommendation, TelemetrySnapshot
from aetheros.policy_engine.rules import (
    detect_cpu_overload,
    detect_disk_pressure,
    detect_idle_state,
    detect_memory_pressure,
)


def _snap(
    *,
    cpu: float = 50.0,
    memory: float = 50.0,
    disk: float = 50.0,
    battery: float | None = None,
) -> TelemetrySnapshot:
    """Build a minimal TelemetrySnapshot for tests."""

    return TelemetrySnapshot(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=disk,
        battery_percent=battery,
        process_count=3,
        top_processes=("a", "b", "c"),
    )


def test_cpu_critical_above_95() -> None:
    """CPU above 95% should yield a critical recommendation."""

    rec = detect_cpu_overload(_snap(cpu=96.0))
    assert rec is not None
    assert rec.level == "critical"
    assert "95" in rec.reason


def test_cpu_warning_above_85() -> None:
    """CPU between 85 and 95 should yield a warning."""

    rec = detect_cpu_overload(_snap(cpu=90.0))
    assert rec is not None
    assert rec.level == "warning"


def test_cpu_ok_returns_none() -> None:
    """CPU at or below 85 should not recommend overload."""

    assert detect_cpu_overload(_snap(cpu=85.0)) is None


def test_memory_warning_above_90() -> None:
    """Memory above 90% should warn."""

    rec = detect_memory_pressure(_snap(memory=91.0))
    assert rec is not None
    assert rec.level == "warning"


def test_disk_critical_above_95() -> None:
    """Disk above 95% should be critical."""

    rec = detect_disk_pressure(_snap(disk=96.0))
    assert rec is not None
    assert rec.level == "critical"


def test_idle_when_cpu_and_memory_low() -> None:
    """Low CPU and memory should report idle."""

    rec = detect_idle_state(_snap(cpu=10.0, memory=30.0))
    assert rec is not None
    assert rec.level == "normal"
    assert rec.title == "Idle System"


def test_idle_not_triggered_when_busy() -> None:
    """Busy CPU should not be classified as idle."""

    assert detect_idle_state(_snap(cpu=20.0, memory=30.0)) is None


def test_evaluate_all_sorts_critical_before_warning() -> None:
    """evaluate_all should put critical recommendations first."""

    snapshot = _snap(cpu=96.0, memory=91.0, disk=50.0)
    results = PolicyEngine().evaluate_all(snapshot)
    assert results[0].level == "critical"
    assert any(r.level == "warning" for r in results)


def test_evaluate_returns_top_severity() -> None:
    """evaluate should return the single most severe finding."""

    snapshot = _snap(cpu=96.0, memory=91.0)
    top = PolicyEngine().evaluate(snapshot)
    assert top is not None
    assert top.level == "critical"


def test_confidence_out_of_range_rejected() -> None:
    """PolicyRecommendation must reject invalid confidence."""

    with pytest.raises(ValueError, match="confidence"):
        PolicyRecommendation(
            level="warning",
            title="Bad",
            reason="x",
            recommended_action="y",
            confidence=150,
        )


def test_healthy_snapshot_has_no_issues() -> None:
    """Mid-range usage should produce no warning/critical recommendations."""

    results = PolicyEngine().evaluate_all(_snap(cpu=40.0, memory=50.0, disk=40.0))
    issues = [r for r in results if r.level in ("warning", "critical")]
    assert issues == []
