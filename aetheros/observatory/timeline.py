"""Scrolling system-event timeline for the observatory."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from aetheros.observatory.models import SystemEvent

DEFAULT_EVENT_CAPACITY = 200


@dataclass
class EventTimeline:
    """In-memory scrolling timeline backed by recorded SystemEvents.

    Args:
        capacity: Maximum events retained in memory.
    """

    capacity: int = DEFAULT_EVENT_CAPACITY
    scroll_offset: int = 0
    _events: deque[SystemEvent] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Allocate the event deque."""

        self._events = deque(maxlen=self.capacity)

    def __len__(self) -> int:
        """Return stored event count."""

        return len(self._events)

    def add(self, event: SystemEvent) -> None:
        """Append an event and jump to the live edge."""

        self._events.append(event)
        self.scroll_offset = 0

    def append_keep_scroll(self, event: SystemEvent) -> None:
        """Append without resetting scroll position."""

        self._events.append(event)

    def add_many(self, events: list[SystemEvent]) -> None:
        """Append multiple events."""

        for event in events:
            self.add(event)

    def scroll(self, delta: int) -> None:
        """Shift the visible window (positive = older)."""

        if not self._events:
            self.scroll_offset = 0
            return
        max_offset = max(0, len(self._events) - 1)
        self.scroll_offset = max(0, min(max_offset, self.scroll_offset + delta))

    def visible(self, limit: int = 8) -> tuple[SystemEvent, ...]:
        """Return the visible event slice oldest → newest."""

        if not self._events:
            return ()
        limit = max(1, limit)
        end = len(self._events) - self.scroll_offset
        start = max(0, end - limit)
        return tuple(list(self._events)[start:end])

    def recent(self, limit: int = 20) -> tuple[SystemEvent, ...]:
        """Return the newest events for observation derivation."""

        if not self._events:
            return ()
        items = list(self._events)
        return tuple(items[-limit:])
