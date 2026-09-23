"""HistoryRecorder — SQLite + rolling in-memory telemetry history.

Append-only persistence. Never overwrites prior rows. Never runs OS commands.
"""

from __future__ import annotations

import sqlite3
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aetheros.observatory.models import SystemEvent, TelemetryPoint, TimelineWindow
from aetheros.policy_engine.models import TelemetrySnapshot

DEFAULT_CAPACITY = 300

_CREATE_TELEMETRY = """
CREATE TABLE IF NOT EXISTS telemetry_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    cpu REAL NOT NULL,
    memory REAL NOT NULL,
    disk REAL NOT NULL,
    battery REAL,
    intent TEXT NOT NULL
);
"""

_CREATE_EVENTS = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL
);
"""

_INSERT_TELEMETRY = """
INSERT INTO telemetry_history (timestamp, cpu, memory, disk, battery, intent)
VALUES (?, ?, ?, ?, ?, ?);
"""

_INSERT_EVENT = """
INSERT INTO events (timestamp, type, severity, title, description)
VALUES (?, ?, ?, ?, ?);
"""


@dataclass
class HistoryRecorder:
    """Record telemetry and events with SQLite + a 300-sample memory window.

    Args:
        db_path: Path to observatory.db.
        capacity: In-memory rolling capacity (default 300).
    """

    db_path: Path = field(default_factory=lambda: Path("data/observatory.db"))
    capacity: int = DEFAULT_CAPACITY
    _points: deque[TelemetryPoint] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Create tables and allocate the ring buffer."""

        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._points = deque(maxlen=self.capacity)
        with self._connect() as conn:
            conn.execute(_CREATE_TELEMETRY)
            conn.execute(_CREATE_EVENTS)
            conn.commit()

    def __len__(self) -> int:
        """Return in-memory sample count."""

        return len(self._points)

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection."""

        return sqlite3.connect(self.db_path)

    def record_telemetry(
        self,
        snapshot: TelemetrySnapshot,
        intent: str,
    ) -> TelemetryPoint:
        """Store one telemetry snapshot (memory + SQLite append)."""

        point = TelemetryPoint(
            timestamp=snapshot.timestamp,
            cpu=snapshot.cpu_percent,
            memory=snapshot.memory_percent,
            disk=snapshot.disk_percent,
            battery=snapshot.battery_percent,
            intent=intent,
        )
        self._points.append(point)
        with self._connect() as conn:
            conn.execute(
                _INSERT_TELEMETRY,
                (
                    point.timestamp.isoformat(),
                    point.cpu,
                    point.memory,
                    point.disk,
                    point.battery,
                    point.intent,
                ),
            )
            conn.commit()
        return point

    def record_event(self, event: SystemEvent) -> None:
        """Append one system event (never overwrites)."""

        with self._connect() as conn:
            conn.execute(
                _INSERT_EVENT,
                (
                    event.timestamp.isoformat(),
                    event.type,
                    event.severity,
                    event.title,
                    event.description,
                ),
            )
            conn.commit()

    def latest(self) -> TelemetryPoint | None:
        """Return the newest in-memory point."""

        return self._points[-1] if self._points else None

    def points(self) -> tuple[TelemetryPoint, ...]:
        """Return in-memory points oldest → newest."""

        return tuple(self._points)

    def get_last_seconds(self, seconds: int) -> tuple[TelemetryPoint, ...]:
        """Return in-memory points from the last N seconds."""

        return self._filter_since(timedelta(seconds=seconds))

    def get_last_minutes(self, minutes: int) -> tuple[TelemetryPoint, ...]:
        """Return in-memory points from the last N minutes."""

        return self._filter_since(timedelta(minutes=minutes))

    def timeline_windows(self) -> TimelineWindow:
        """Build the standard 60s / 5m / 1h windows."""

        return TimelineWindow(
            last_60_seconds=self.get_last_seconds(60),
            last_5_minutes=self.get_last_minutes(5),
            last_hour=self.get_last_minutes(60),
        )

    def series(self, metric: str, points: tuple[TelemetryPoint, ...] | None = None) -> tuple[float, ...]:
        """Extract a metric series from points (default: all memory)."""

        source = points if points is not None else self.points()
        if metric == "memory":
            return tuple(p.memory for p in source)
        if metric == "disk":
            return tuple(p.disk for p in source)
        return tuple(p.cpu for p in source)

    def window(self, *, offset: int, width: int, metric: str) -> tuple[float, ...]:
        """Return a graph window shifted by offset from the live edge."""

        values = self.series(metric)
        if not values:
            return ()
        width = max(1, width)
        end = len(values) - max(0, offset)
        if end <= 0:
            return ()
        start = max(0, end - width)
        return values[start:end]

    def _filter_since(self, delta: timedelta) -> tuple[TelemetryPoint, ...]:
        """Filter in-memory points newer than now - delta."""

        if not self._points:
            return ()
        newest = self._points[-1].timestamp
        if newest.tzinfo is None:
            newest = newest.replace(tzinfo=timezone.utc)
        cutoff = newest - delta
        return tuple(p for p in self._points if _aware(p.timestamp) >= cutoff)


def _aware(value: datetime) -> datetime:
    """Ensure a datetime is timezone-aware UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
