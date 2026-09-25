"""Immutable consensus events — sole cross-agent contract for P4.

Agents never call peers directly. Events are frozen and carry only
public systems payloads (no personal content).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class Event:
    """One immutable message on the consensus event bus.

    Attributes:
        id: Opaque unique identifier.
        sender: Producing agent id.
        receiver: Target agent id, or ``"*"`` for broadcast.
        type: Event type string (e.g. ``agent.finding``).
        payload: Structured public systems body.
        timestamp: UTC creation time.
    """

    id: str
    sender: str
    receiver: str
    type: str
    payload: tuple[tuple[str, str], ...]
    timestamp: datetime

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("event id must be non-empty")
        if not self.sender.strip():
            raise ValueError("sender must be non-empty")
        if not self.receiver.strip():
            raise ValueError("receiver must be non-empty")
        if not self.type.strip():
            raise ValueError("type must be non-empty")

    def payload_dict(self) -> dict[str, str]:
        """Materialize payload as a plain dict (copy)."""

        return dict(self.payload)


def make_consensus_event(
    *,
    sender: str,
    receiver: str,
    type: str,
    payload: dict[str, Any] | None = None,
    event_id: str | None = None,
    timestamp: datetime | None = None,
) -> Event:
    """Construct an immutable ``Event`` with stringified payload pairs."""

    raw = payload or {}
    pairs = tuple(
        (str(key), _stringify(value))
        for key, value in sorted(raw.items(), key=lambda i: str(i[0]))
    )
    return Event(
        id=event_id or uuid4().hex,
        sender=sender,
        receiver=receiver,
        type=type,
        payload=pairs,
        timestamp=timestamp or datetime.now(UTC),
    )


def _stringify(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if isinstance(value, (list, tuple)):
        return "|".join(_stringify(v) for v in value)
    return str(value)
