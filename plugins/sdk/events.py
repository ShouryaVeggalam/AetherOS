"""Event subscriptions — plugins receive immutable topic notifications.

Publishers push frozen event payloads. Plugins never mutate the bus.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class PluginEvent:
    """Immutable event delivered to subscribers."""

    topic: str
    payload: Mapping[str, Any]
    emitted_at: datetime
    source: str = "host"

    def __post_init__(self) -> None:
        if not self.topic.strip():
            raise ValueError("topic must be non-empty")


EventHandler = Callable[[PluginEvent], None]


@dataclass
class EventBus:
    """Synchronous in-process pub/sub for sandboxed plugins."""

    _subs: dict[str, list[EventHandler]] = field(default_factory=dict)
    _history: list[PluginEvent] = field(default_factory=list)

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Subscribe ``handler`` to ``topic`` (exact match)."""

        key = topic.strip()
        if not key:
            raise ValueError("topic must be non-empty")
        self._subs.setdefault(key, []).append(handler)

    def unsubscribe(self, topic: str, handler: EventHandler) -> None:
        """Remove a previously registered handler if present."""

        handlers = self._subs.get(topic.strip(), [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(
        self,
        topic: str,
        payload: Mapping[str, Any] | None = None,
        *,
        source: str = "host",
        now: datetime | None = None,
    ) -> PluginEvent:
        """Publish an immutable event and invoke matching handlers."""

        event = PluginEvent(
            topic=topic.strip(),
            payload=dict(payload or {}),
            emitted_at=now or datetime.now(UTC),
            source=source,
        )
        self._history.append(event)
        for handler in list(self._subs.get(event.topic, ())):
            handler(event)
        return event

    def history(self, *, limit: int = 50) -> tuple[PluginEvent, ...]:
        """Return recent events (newest last), capped by ``limit``."""

        if limit <= 0:
            return ()
        return tuple(self._history[-limit:])

    def topics(self) -> tuple[str, ...]:
        """Return topics that currently have subscribers."""

        return tuple(sorted(self._subs))
