"""Local transport abstraction for cluster telemetry.

JSON messages only. Designed so a WebSocket transport can be added later.
No SSH, no remote shell, no network command execution.
"""

from __future__ import annotations

import json
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class TransportMessage:
    """One immutable JSON-serializable cluster message.

    Attributes:
        kind: Message kind (telemetry, heartbeat).
        payload: JSON-compatible dictionary.
        published_at: UTC time the message entered the bus.
    """

    kind: str
    payload: dict[str, Any]
    published_at: datetime

    def to_json(self) -> str:
        """Serialize this message to a JSON string."""

        body = {
            "kind": self.kind,
            "payload": self.payload,
            "published_at": self.published_at.isoformat(),
        }
        return json.dumps(body, separators=(",", ":"))

    @classmethod
    def from_json(cls, raw: str) -> TransportMessage:
        """Deserialize a JSON string into a TransportMessage."""

        data = json.loads(raw)
        stamp = datetime.fromisoformat(str(data["published_at"]))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=UTC)
        return cls(
            kind=str(data["kind"]),
            payload=dict(data["payload"]),
            published_at=stamp,
        )


class ClusterTransport(Protocol):
    """Publish/subscribe interface for cluster agents and the dashboard."""

    def publish(self, snapshot: TransportMessage) -> None:
        """Publish one message onto the bus."""

    def subscribe(self, *, max_messages: int = 100) -> tuple[TransportMessage, ...]:
        """Drain pending messages for subscribers (non-blocking)."""


@dataclass
class LocalJSONTransport:
    """In-process JSON message bus (WebSocket-ready shape).

    Messages are stored as JSON strings so the on-wire format matches a
    future network transport. Thread-safe for agent + dashboard use.
    """

    capacity: int = 500
    _queue: deque[str] = field(default_factory=deque, init=False, repr=False)
    _lock: threading.Lock = field(
        default_factory=threading.Lock, init=False, repr=False
    )

    def __post_init__(self) -> None:
        """Allocate the bounded JSON queue."""

        if self.capacity <= 0:
            raise ValueError("capacity must be positive")
        self._queue = deque(maxlen=self.capacity)

    def publish(self, snapshot: TransportMessage) -> None:
        """Enqueue one JSON-encoded message."""

        encoded = snapshot.to_json()
        with self._lock:
            self._queue.append(encoded)

    def subscribe(self, *, max_messages: int = 100) -> tuple[TransportMessage, ...]:
        """Pop up to `max_messages` pending messages (oldest first)."""

        limit = max(1, max_messages)
        out: list[TransportMessage] = []
        with self._lock:
            while self._queue and len(out) < limit:
                raw = self._queue.popleft()
                out.append(TransportMessage.from_json(raw))
        return tuple(out)

    def pending(self) -> int:
        """Return the number of unread messages."""

        with self._lock:
            return len(self._queue)


def utc_now() -> datetime:
    """Return timezone-aware UTC now."""

    return datetime.now(UTC)
