"""Unit tests for Phase 1 telemetry models, collector, and engine."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from aetheros.telemetry.collector import TelemetryCollector
from aetheros.telemetry.engine import TelemetryEngine
from aetheros.telemetry.models import (
    BatterySnapshot,
    CpuSnapshot,
    DiskSnapshot,
    MemorySnapshot,
    ProcessSnapshot,
    SystemSnapshot,
    utc_now,
)


def test_utc_now_is_timezone_aware() -> None:
    """utc_now should return an aware UTC datetime."""

    now = utc_now()
    assert now.tzinfo is not None
    assert now.tzinfo.utcoffset(now) == UTC.utcoffset(now)


def test_system_snapshot_is_immutable() -> None:
    """Frozen dataclasses must reject attribute assignment."""

    snapshot = SystemSnapshot(
        collected_at=datetime(2026, 1, 1, tzinfo=UTC),
        cpu=CpuSnapshot(
            percent=10.0, per_cpu_percent=(10.0,), load_avg=(0.1, 0.2, 0.3)
        ),
        memory=MemorySnapshot(
            total_bytes=8,
            available_bytes=4,
            used_bytes=4,
            percent=50.0,
            swap_total_bytes=0,
            swap_used_bytes=0,
            swap_percent=0.0,
        ),
        disks=(
            DiskSnapshot(
                mountpoint="/",
                total_bytes=100,
                used_bytes=40,
                free_bytes=60,
                percent=40.0,
            ),
        ),
        processes=(),
        battery=None,
    )
    with pytest.raises((AttributeError, TypeError)):
        snapshot.cpu = snapshot.cpu  # type: ignore[misc]


def test_engine_rejects_non_positive_interval() -> None:
    """Interval must be greater than zero."""

    with pytest.raises(ValueError, match="positive"):
        TelemetryEngine(interval_seconds=0)


def test_engine_collect_once_delegates_to_collector() -> None:
    """collect_once should return whatever the collector produces."""

    fake = MagicMock(spec=TelemetryCollector)
    expected = MagicMock(spec=SystemSnapshot)
    fake.collect.return_value = expected
    engine = TelemetryEngine(collector=fake, interval_seconds=1.0)
    assert engine.collect_once() is expected
    fake.collect.assert_called_once()


def test_engine_run_notifies_callback_then_stops() -> None:
    """run() should invoke the callback and honor stop()."""

    fake = MagicMock(spec=TelemetryCollector)
    fake.collect.return_value = MagicMock(spec=SystemSnapshot)
    engine = TelemetryEngine(collector=fake, interval_seconds=0.01)
    seen: list[object] = []

    def on_snapshot(snapshot: SystemSnapshot) -> None:
        """Record the snapshot and stop after the first sample."""

        seen.append(snapshot)
        engine.stop()

    with patch("aetheros.telemetry.engine.time.sleep", return_value=None):
        engine.run(on_snapshot=on_snapshot)

    assert len(seen) == 1
    assert engine.is_running is False


def test_collector_collect_returns_populated_snapshot() -> None:
    """Live collector should return a real snapshot with core fields set.

    This integration-style test talks to the host via psutil but only
    reads data — it never mutates the system.
    """

    collector = TelemetryCollector(disk_mounts=("/",), process_limit=5)
    # Two collects so process cpu_percent has a prior baseline.
    collector.collect()
    snapshot = collector.collect()

    assert isinstance(snapshot.collected_at, datetime)
    assert 0.0 <= snapshot.cpu.percent <= 100.0
    assert snapshot.memory.total_bytes > 0
    assert len(snapshot.disks) >= 1
    assert snapshot.disks[0].mountpoint == "/"
    assert len(snapshot.processes) <= 5
    if snapshot.battery is not None:
        assert isinstance(snapshot.battery, BatterySnapshot)
        assert 0.0 <= snapshot.battery.percent <= 100.0


def test_process_snapshot_fields() -> None:
    """ProcessSnapshot should store the expected identity fields."""

    proc = ProcessSnapshot(
        pid=1,
        name="init",
        username="root",
        cpu_percent=0.5,
        memory_percent=0.1,
        status="sleeping",
    )
    assert proc.pid == 1
    assert proc.name == "init"
