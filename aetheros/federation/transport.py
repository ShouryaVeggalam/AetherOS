"""Federation transport — local in-process message bus only.

Read-only exchange of serialized protocol messages. No sockets to remote
shells, no SSH, no command channels. Suitable for demo peers and tests.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field

from aetheros.federation.protocol import ProtocolMessage
from aetheros.federation.serializer import decode_message, encode_message


@dataclass
class LocalTransport:
    """In-memory FIFO of versioned federation messages.

    Publishers enqueue encoded bytes. Consumers drain and decode. Never
    executes payloads — payloads are observational only.
    """

    maxsize: int = 1024
    _queue: deque[bytes] = field(default_factory=deque)

    def __post_init__(self) -> None:
        if self.maxsize < 1:
            raise ValueError("maxsize must be >= 1")
        self._queue = deque(maxlen=self.maxsize)

    def publish(self, message: ProtocolMessage) -> bytes:
        """Encode and enqueue a message; returns the encoded bytes."""

        raw = encode_message(message)
        self._queue.append(raw)
        return raw

    def publish_raw(self, raw: bytes) -> None:
        """Enqueue pre-encoded bytes (must be valid JSON protocol)."""

        # Validate before enqueue so poison messages fail at the edge.
        decode_message(raw)
        self._queue.append(raw)

    def drain(self, *, limit: int = 100) -> tuple[ProtocolMessage, ...]:
        """Decode up to ``limit`` pending messages (FIFO)."""

        out: list[ProtocolMessage] = []
        for _ in range(max(0, limit)):
            if not self._queue:
                break
            raw = self._queue.popleft()
            out.append(decode_message(raw))
        return tuple(out)

    def peek_count(self) -> int:
        return len(self._queue)

    def clear(self) -> None:
        self._queue.clear()


@dataclass
class TransportHub:
    """Fan-out hub connecting multiple named local transports.

    Used for multi-node demos on one host. Still no remote execution.
    """

    _peers: dict[str, LocalTransport] = field(default_factory=dict)

    def register(
        self, node_id: str, transport: LocalTransport | None = None
    ) -> LocalTransport:
        if not node_id.strip():
            raise ValueError("node_id must be non-empty")
        bus = transport if transport is not None else LocalTransport()
        self._peers[node_id] = bus
        return bus

    def publish_to(
        self,
        recipients: Iterable[str],
        message: ProtocolMessage,
    ) -> int:
        """Publish a copy of ``message`` to each recipient transport."""

        count = 0
        for node_id in recipients:
            bus = self._peers.get(node_id)
            if bus is None:
                continue
            bus.publish(message)
            count += 1
        return count

    def broadcast(
        self,
        message: ProtocolMessage,
        *,
        exclude: str | None = None,
    ) -> int:
        """Publish to all peers except optional ``exclude`` source."""

        recipients = [nid for nid in self._peers if exclude is None or nid != exclude]
        return self.publish_to(recipients, message)

    def get(self, node_id: str) -> LocalTransport | None:
        return self._peers.get(node_id)

    def __len__(self) -> int:
        return len(self._peers)
