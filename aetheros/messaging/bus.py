"""Async in-process message bus for agent collaboration.

Agents subscribe by id (and optionally by event type). Publish is
non-blocking for the caller; delivery fans out to matching queues.
No network I/O — userspace, in-process only.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass, field

from aetheros.messaging.event import AgentEvent
from aetheros.messaging.protocol import BROADCAST


@dataclass
class AsyncMessageBus:
    """Fan-out publish/subscribe bus backed by ``asyncio.Queue``.

    Attributes:
        history_limit: Max retained events for UI / debugging.
    """

    history_limit: int = 200
    _queues: dict[str, list[asyncio.Queue[AgentEvent]]] = field(
        default_factory=lambda: defaultdict(list),
        init=False,
        repr=False,
    )
    _history: list[AgentEvent] = field(default_factory=list, init=False, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False, repr=False)

    def subscribe(
        self,
        agent_id: str,
        *,
        maxsize: int = 64,
    ) -> asyncio.Queue[AgentEvent]:
        """Register a delivery queue for ``agent_id`` (and broadcasts)."""

        queue: asyncio.Queue[AgentEvent] = asyncio.Queue(maxsize=maxsize)
        self._queues[agent_id].append(queue)
        return queue

    async def publish(self, event: AgentEvent) -> int:
        """Deliver ``event`` to matching subscribers. Returns delivery count."""

        async with self._lock:
            self._history.append(event)
            if len(self._history) > self.history_limit:
                overflow = len(self._history) - self.history_limit
                del self._history[:overflow]

        targets: list[asyncio.Queue[AgentEvent]] = []
        if event.receiver == BROADCAST:
            for queues in self._queues.values():
                targets.extend(queues)
        else:
            targets.extend(self._queues.get(event.receiver, []))
            # Sender inbox also sees own traffic when subscribed as receiver.
            if event.sender != event.receiver:
                targets.extend(self._queues.get(event.sender, []))

        delivered = 0
        seen: set[int] = set()
        for queue in targets:
            qid = id(queue)
            if qid in seen:
                continue
            seen.add(qid)
            try:
                queue.put_nowait(event)
                delivered += 1
            except asyncio.QueueFull:
                # Drop oldest to keep the bus moving under pressure.
                try:
                    _ = queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    queue.put_nowait(event)
                    delivered += 1
                except asyncio.QueueFull:
                    continue
        return delivered

    def history(self, *, limit: int = 50) -> tuple[AgentEvent, ...]:
        """Return recent events newest-last (immutable copy)."""

        if limit <= 0:
            return ()
        return tuple(self._history[-limit:])

    def latest_for(self, sender: str) -> AgentEvent | None:
        """Return the most recent event from ``sender``, if any."""

        for event in reversed(self._history):
            if event.sender == sender:
                return event
        return None

    def clear(self) -> None:
        """Drop history and detach all subscriber queues."""

        self._history.clear()
        self._queues.clear()
