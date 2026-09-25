"""Immutable agent message events.

Events are the only cross-agent contract. Agents never call each other
directly — they publish and consume these records via the message bus.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class AgentEvent:
    """One structured message on the agent bus.

    Attributes:
        id: Opaque unique identifier.
        sender: Agent id that produced the event.
        receiver: Target agent id, or ``"*"`` for broadcast.
        type: Protocol event type (see ``protocol.EventType``).
        payload: JSON-serializable structured body.
        timestamp: UTC time the event was created.
    """

    id: str
    sender: str
    receiver: str
    type: str
    payload: dict[str, Any]
    timestamp: datetime

    def __post_init__(self) -> None:
        """Reject empty identity fields."""

        if not self.id.strip():
            raise ValueError("event id must be non-empty")
        if not self.sender.strip():
            raise ValueError("sender must be non-empty")
        if not self.receiver.strip():
            raise ValueError("receiver must be non-empty")
        if not self.type.strip():
            raise ValueError("type must be non-empty")


def make_event(
    *,
    sender: str,
    receiver: str,
    type: str,
    payload: dict[str, Any] | None = None,
    event_id: str | None = None,
    timestamp: datetime | None = None,
) -> AgentEvent:
    """Construct an immutable ``AgentEvent`` with defaults filled in."""

    return AgentEvent(
        id=event_id or uuid4().hex,
        sender=sender,
        receiver=receiver,
        type=type,
        payload=dict(payload or {}),
        timestamp=timestamp or datetime.now(UTC),
    )
