"""Telemetry engine: continuous collection on a fixed interval.

Think of this as a metronome. Every N seconds it asks the collector
for a fresh snapshot and hands that snapshot to any registered listeners
(for example a Rich UI, or later a policy engine).
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterator
from typing import Protocol

from aetheros.telemetry.collector import TelemetryCollector
from aetheros.telemetry.models import SystemSnapshot


class SnapshotListener(Protocol):
    """Anything that wants to receive each new SystemSnapshot."""

    def on_snapshot(self, snapshot: SystemSnapshot) -> None:
        """Handle one telemetry sample."""


class TelemetryEngine:
    """Runs a collect → notify loop at a fixed interval.

    Args:
        collector: Source of SystemSnapshot values.
        interval_seconds: Seconds to wait between samples (Phase 1: 1.0).
    """

    def __init__(
        self,
        collector: TelemetryCollector | None = None,
        interval_seconds: float = 1.0,
    ) -> None:
        """Create an engine with an optional custom collector."""

        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self._collector = collector or TelemetryCollector()
        self._interval_seconds = interval_seconds
        self._listeners: list[SnapshotListener] = []
        self._running = False

    @property
    def is_running(self) -> bool:
        """Return True while the engine loop is active."""

        return self._running

    def add_listener(self, listener: SnapshotListener) -> None:
        """Register a listener that receives every new snapshot."""

        self._listeners.append(listener)

    def remove_listener(self, listener: SnapshotListener) -> None:
        """Unregister a previously added listener."""

        self._listeners = [item for item in self._listeners if item is not listener]

    def collect_once(self) -> SystemSnapshot:
        """Take a single snapshot without starting the loop."""

        return self._collector.collect()

    def stream(self) -> Iterator[SystemSnapshot]:
        """Yield snapshots forever at the configured interval.

        Yields:
            Fresh SystemSnapshot values, spaced by interval_seconds.
        """

        self._running = True
        try:
            while self._running:
                snapshot = self._collector.collect()
                yield snapshot
                time.sleep(self._interval_seconds)
        finally:
            self._running = False

    def run(self, on_snapshot: Callable[[SystemSnapshot], None] | None = None) -> None:
        """Collect forever and notify listeners (and an optional callback).

        Args:
            on_snapshot: Optional callable invoked with each snapshot.
                Useful for simple scripts without a full listener object.

        Raises:
            KeyboardInterrupt: Propagated when the user presses Ctrl+C so
                callers can shut down cleanly.
        """

        self._running = True
        try:
            while self._running:
                snapshot = self._collector.collect()
                for listener in self._listeners:
                    listener.on_snapshot(snapshot)
                if on_snapshot is not None:
                    on_snapshot(snapshot)
                time.sleep(self._interval_seconds)
        except KeyboardInterrupt:
            raise
        finally:
            self._running = False

    def stop(self) -> None:
        """Request the engine loop to stop after the current iteration."""

        self._running = False
