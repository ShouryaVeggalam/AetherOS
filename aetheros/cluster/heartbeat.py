"""Heartbeat tracking for cluster node liveness.

Determines online/offline from last_seen age. Read-only — no actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from aetheros.cluster.models import Heartbeat
from aetheros.cluster.transport import TransportMessage, utc_now

DEFAULT_ONLINE_WINDOW_SECONDS = 5.0


@dataclass
class HeartbeatTracker:
    """Track heartbeats and decide which nodes are online.

    Args:
        online_window_seconds: Max age for a node to count as online.
    """

    online_window_seconds: float = DEFAULT_ONLINE_WINDOW_SECONDS
    _last: dict[str, Heartbeat] = field(default_factory=dict, init=False, repr=False)

    def record(self, heartbeat: Heartbeat) -> None:
        """Store the newest heartbeat for a node."""

        previous = self._last.get(heartbeat.node_id)
        if previous is None or _aware(heartbeat.timestamp) >= _aware(
            previous.timestamp
        ):
            self._last[heartbeat.node_id] = heartbeat

    def record_seen(
        self, node_id: str, timestamp: datetime, *, online: bool = True
    ) -> None:
        """Record an implicit heartbeat from a telemetry update."""

        self.record(Heartbeat(node_id=node_id, timestamp=timestamp, online=online))

    def is_online(self, node_id: str, *, now: datetime | None = None) -> bool:
        """Return True when the node was seen within the online window."""

        beat = self._last.get(node_id)
        if beat is None or not beat.online:
            return False
        current = now or utc_now()
        age = (_aware(current) - _aware(beat.timestamp)).total_seconds()
        return age <= self.online_window_seconds

    def offline_ids(
        self, node_ids: tuple[str, ...], *, now: datetime | None = None
    ) -> tuple[str, ...]:
        """Return node_ids that are currently offline."""

        return tuple(nid for nid in node_ids if not self.is_online(nid, now=now))

    def heartbeat_from_message(self, message: TransportMessage) -> Heartbeat | None:
        """Decode a heartbeat TransportMessage, or None if wrong kind."""

        if message.kind != "heartbeat":
            return None
        payload = message.payload
        stamp = payload.get("timestamp")
        if stamp is None:
            when = message.published_at
        else:
            when = datetime.fromisoformat(str(stamp))
            if when.tzinfo is None:
                when = when.replace(tzinfo=UTC)
        return Heartbeat(
            node_id=str(payload["node_id"]),
            timestamp=when,
            online=bool(payload.get("online", True)),
        )


def make_heartbeat_message(node_id: str, *, online: bool = True) -> TransportMessage:
    """Build a heartbeat TransportMessage for publishing."""

    stamp = utc_now()
    return TransportMessage(
        kind="heartbeat",
        payload={
            "node_id": node_id,
            "timestamp": stamp.isoformat(),
            "online": online,
        },
        published_at=stamp,
    )


def _aware(value: datetime) -> datetime:
    """Ensure timezone-aware UTC."""

    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
