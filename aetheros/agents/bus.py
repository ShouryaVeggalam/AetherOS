"""Synchronous publish/subscribe bus for P4 multi-agent consensus.

Deterministic, in-process, no network I/O. Distinct from
``aetheros.messaging.AsyncMessageBus`` used by the legacy agentic runtime.
Never mutates published events.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field

from aetheros.agents.events import Event

BROADCAST = "*"
Subscriber = Callable[[Event], None]


@dataclass
class EventBus:
    """Fan-out publish/subscribe bus for immutable consensus events.

    Attributes:
        history_limit: Max retained events for UI / debugging.
    """

    history_limit: int = 200
    _subscribers: dict[str, list[Subscriber]] = field(
        default_factory=lambda: defaultdict(list),
        init=False,
        repr=False,
    )
    _history: list[Event] = field(default_factory=list, init=False, repr=False)

    def subscribe(self, agent_id: str, handler: Subscriber) -> None:
        """Register ``handler`` for events addressed to ``agent_id`` or broadcast."""

        if not agent_id.strip():
            raise ValueError("agent_id must be non-empty")
        self._subscribers[agent_id].append(handler)

    def unsubscribe(self, agent_id: str, handler: Subscriber | None = None) -> None:
        """Remove one handler or all handlers for ``agent_id``."""

        if handler is None:
            self._subscribers.pop(agent_id, None)
            return
        handlers = self._subscribers.get(agent_id, [])
        self._subscribers[agent_id] = [h for h in handlers if h is not handler]

    def publish(self, event: Event) -> int:
        """Deliver ``event`` to matching subscribers. Returns delivery count."""

        self._history.append(event)
        if len(self._history) > self.history_limit:
            overflow = len(self._history) - self.history_limit
            del self._history[:overflow]

        targets: list[Subscriber] = []
        if event.receiver == BROADCAST:
            for handlers in self._subscribers.values():
                targets.extend(handlers)
        else:
            targets.extend(self._subscribers.get(event.receiver, ()))
            if event.sender != event.receiver:
                targets.extend(self._subscribers.get(event.sender, ()))

        delivered = 0
        seen: set[int] = set()
        for handler in targets:
            hid = id(handler)
            if hid in seen:
                continue
            seen.add(hid)
            handler(event)
            delivered += 1
        return delivered

    def history(self, *, limit: int = 50) -> tuple[Event, ...]:
        """Return recent events newest-last."""

        if limit <= 0:
            return ()
        return tuple(self._history[-limit:])

    def clear(self) -> None:
        """Drop history and detach all subscribers."""

        self._history.clear()
        self._subscribers.clear()
