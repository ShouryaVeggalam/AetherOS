"""Unit tests for dashboard formatting helpers (coverage outside Live loop)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from aetheros.dashboard.formatting import (
    format_audit_summary,
    format_battery,
    format_uptime,
    plugin_console_rows,
    relative_time,
)
from aetheros.sdk.registry import PluginRecord
from aetheros.telemetry.models import (
    BatterySnapshot,
    CpuSnapshot,
    DiskSnapshot,
    MemorySnapshot,
    SystemSnapshot,
)


def _system(*, battery: BatterySnapshot | None) -> SystemSnapshot:
    """Minimal system snapshot for formatter tests."""

    return SystemSnapshot(
        collected_at=datetime.now(UTC),
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
        battery=battery,
    )


def test_format_uptime_bands() -> None:
    """Uptime formatter should cover minutes, hours, and days."""

    assert format_uptime(45) == "0m 45s"
    assert "h" in format_uptime(3700)
    assert "d" in format_uptime(90_000)


def test_format_battery_and_audit() -> None:
    """Battery and audit summaries should be human-readable."""

    assert format_battery(_system(battery=None)) == "n/a"
    assert "80%" in format_battery(_system(battery=BatterySnapshot(80.0, True, None)))
    assert "battery" in format_battery(
        _system(battery=BatterySnapshot(40.0, False, 3600))
    )
    assert "No audit" in format_audit_summary(None)


def test_relative_time_deterministic() -> None:
    """relative_time should honor an injected clock."""

    now = datetime(2026, 1, 2, 12, 0, tzinfo=UTC)
    stamp = (now - timedelta(seconds=30)).isoformat()
    assert relative_time(stamp, now=now) == "30s ago"
    assert relative_time("not-a-stamp", now=now) == "recently"


def test_plugin_console_rows() -> None:
    """Plugin rows should encode verified/enabled state for the console."""

    rows = plugin_console_rows(
        [
            PluginRecord(
                name="Safe",
                version="1.0.0",
                author="AetherOS",
                description="ok",
                path=Path("."),
                enabled=True,
                verified=True,
                safety_reason="ok",
            ),
            PluginRecord(
                name="Bad",
                version="0.0.1",
                author="x",
                description="no",
                path=Path("."),
                enabled=False,
                verified=False,
                safety_reason="unsafe",
            ),
        ]
    )
    assert rows[0][2] == "Enabled"
    assert rows[0][4] == "Verified"
    assert rows[1][2] == "Rejected"
    assert rows[1][4] == "Unsafe"
