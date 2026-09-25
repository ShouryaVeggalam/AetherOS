"""Fabric transport — in-process eventual-consistency bus.

Delivers immutable events between federated identities in-memory.
Never opens network sockets. Never executes remote actions.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from aetheros.protocol.events import FabricEvent
from aetheros.protocol.versioning import FABRIC_PROTOCOL


@dataclass
class InProcessTransport:
    """Fan-out mailbox transport for fabric federation.

    Attributes:
        history_limit: Max retained events for sync / UI.
    """

    history_limit: int = 500
    _mailboxes: dict[str, deque[FabricEvent]] = field(
        default_factory=lambda: defaultdict(lambda: deque(maxlen=64)),
        init=False,
        repr=False,
    )
    _history: deque[FabricEvent] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Allocate bounded history."""

        self._history = deque(maxlen=self.history_limit)

    def subscribe(self, node_id: str) -> None:
        """Ensure a mailbox exists for ``node_id``."""

        _ = self._mailboxes[node_id]

    def publish(self, event: FabricEvent) -> int:
        """Deliver ``event`` to all subscribed mailboxes. Returns fan-out count."""

        if not FABRIC_PROTOCOL.compatible_with(event.version):
            return 0
        self._history.append(event)
        delivered = 0
        for node_id, box in list(self._mailboxes.items()):
            box.append(event)
            delivered += 1
            _ = node_id
        return delivered

    def drain(self, node_id: str) -> tuple[FabricEvent, ...]:
        """Pop all pending events for ``node_id``."""

        box = self._mailboxes.get(node_id)
        if not box:
            return ()
        events = tuple(box)
        box.clear()
        return events

    def history(self, *, limit: int = 50) -> tuple[FabricEvent, ...]:
        """Recent events newest-last."""

        if limit <= 0:
            return ()
        items = list(self._history)
        return tuple(items[-limit:])
