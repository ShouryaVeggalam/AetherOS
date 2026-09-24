"""Unit tests for AetherOS v1.1 Observatory recorder and event detector."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from rich.console import Console

from aetheros.observatory import (
    EventTimeline,
    HistoryRecorder,
    ObservatoryPanel,
    derive_observations,
    detect_events,
    render_ascii_graph,
    research_completed_event,
    sparkline,
)
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot


def _snap(
    *,
    cpu: float,
    memory: float = 50.0,
    disk: float = 20.0,
    when: datetime | None = None,
) -> TelemetrySnapshot:
    """Build a TelemetrySnapshot for recorder tests."""

    return TelemetrySnapshot(
        timestamp=when or datetime.now(UTC),
        cpu_percent=cpu,
        memory_percent=memory,
        disk_percent=disk,
        battery_percent=80.0,
        process_count=2,
        top_processes=("a", "b"),
    )


def _point(
    *,
    cpu: float,
    memory: float = 50.0,
    intent: str = "Coding",
    seconds_ago: float = 0.0,
) -> TelemetryPoint:
    """Build a TelemetryPoint relative to now."""

    stamp = datetime.now(UTC) - timedelta(seconds=seconds_ago)
    return TelemetryPoint(stamp, cpu, memory, 20.0, 80.0, intent)


def test_recorder_appends_sqlite_and_memory(tmp_path: Path) -> None:
    """HistoryRecorder should append rows and keep a rolling memory window."""

    db = tmp_path / "observatory.db"
    recorder = HistoryRecorder(db_path=db, capacity=300)
    for value in range(10):
        recorder.record_telemetry(_snap(cpu=float(value)), "Coding")
    assert len(recorder) == 10
    assert recorder.latest() is not None
    assert recorder.latest().cpu == 9.0
    # SQLite append-only: counting rows.
    import sqlite3

    with sqlite3.connect(db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM telemetry_history").fetchone()[0]
    assert count == 10


def test_recorder_capacity_300(tmp_path: Path) -> None:
    """In-memory ring buffer should cap at 300 samples."""

    recorder = HistoryRecorder(db_path=tmp_path / "o.db", capacity=300)
    for _value in range(350):
        recorder.record_telemetry(_snap(cpu=1.0), "Balanced")
    assert len(recorder) == 300


def test_get_last_seconds(tmp_path: Path) -> None:
    """get_last_seconds should filter by timestamp window."""

    recorder = HistoryRecorder(db_path=tmp_path / "t.db", capacity=300)
    base = datetime.now(UTC)
    for offset in range(10):
        recorder.record_telemetry(
            _snap(cpu=float(offset), when=base - timedelta(seconds=9 - offset)),
            "Coding",
        )
    recent = recorder.get_last_seconds(5)
    assert len(recent) >= 1
    assert all(
        (recent[-1].timestamp - point.timestamp).total_seconds() <= 5.5
        for point in recent
    )


def test_cpu_spike_within_5_seconds() -> None:
    """CPU rising >20% within ~5s should emit cpu_spike."""

    history = (
        _point(cpu=30.0, seconds_ago=5),
        _point(cpu=55.0, seconds_ago=0),
    )
    events = detect_events(history, history[-1], history[0])
    assert any(event.type == "cpu_spike" for event in events)


def test_memory_pressure_at_85() -> None:
    """Crossing 85% memory should emit memory_pressure once."""

    prev = _point(cpu=40.0, memory=70.0, seconds_ago=1)
    curr = _point(cpu=40.0, memory=86.0, seconds_ago=0)
    events = detect_events((prev, curr), curr, prev)
    assert any(event.type == "memory_pressure" for event in events)


def test_intent_changed_event() -> None:
    """Intent switches should emit intent_changed."""

    prev = _point(cpu=40.0, intent="Coding", seconds_ago=1)
    curr = _point(cpu=40.0, intent="Gaming", seconds_ago=0)
    events = detect_events((prev, curr), curr, prev)
    assert any(event.type == "intent_changed" for event in events)


def test_observations_from_history() -> None:
    """Observations must be derived from measured history."""

    history = (
        _point(cpu=20.0, memory=90.0, intent="Coding", seconds_ago=120),
        _point(cpu=45.0, memory=60.0, intent="Coding", seconds_ago=0),
    )
    notes = derive_observations(history, ())
    assert any("CPU" in note for note in notes)
    assert any("Memory pressure recovered" in note for note in notes)
    assert any("Coding intent" in note for note in notes)


def test_sparkline_and_panel(tmp_path: Path) -> None:
    """Sparklines and ObservatoryPanel should render."""

    text = sparkline((10, 20, 80, 40), width=16)
    assert len(text) == 16
    panel = ObservatoryPanel(
        focus_metric="cpu",
        cpu_spark=text,
        memory_spark=sparkline((50, 50), width=16),
        disk_spark=sparkline((10, 12), width=16),
        detail_graph=render_ascii_graph((10, 40, 70), width=20, height=3),
        events=(research_completed_event(winner="X", score=90),),
        observations=("CPU increased by 12% over 30s.",),
        history_offset=0,
        sample_count=3,
        capacity=300,
    )
    console = Console(record=True, width=90)
    console.print(panel)
    exported = console.export_text()
    assert "Observatory" in exported
    assert "AI Observations" in exported


def test_event_persisted(tmp_path: Path) -> None:
    """record_event should insert into the events table."""

    import sqlite3

    recorder = HistoryRecorder(db_path=tmp_path / "e.db", capacity=50)
    event = research_completed_event(winner="Boost", score=88)
    recorder.record_event(event)
    with sqlite3.connect(tmp_path / "e.db") as conn:
        row = conn.execute("SELECT title FROM events").fetchone()
    assert row[0] == "Research Completed"


def test_timeline_scroll() -> None:
    """Timeline scroll should change the visible slice."""

    timeline = EventTimeline()
    for index in range(15):
        timeline.add(research_completed_event(winner=f"S{index}", score=float(index)))
    newest = timeline.visible(limit=4)[-1].description
    timeline.scroll(4)
    older = timeline.visible(limit=4)[-1].description
    assert older != newest
