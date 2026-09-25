"""Fabric protocol events — immutable federation messages.

Nodes publish telemetry snapshots as events. Never carry executable
payloads or remote action directives.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from aetheros.protocol.versioning import FABRIC_PROTOCOL, ProtocolVersion

EventKind = Literal[
    "telemetry.snapshot",
    "federation.heartbeat",
    "sync.ack",
    "twin.scenario",
    "knowledge.announce",
]


@dataclass(frozen=True, slots=True)
class FabricEvent:
    """One immutable fabric protocol event.

    Attributes:
        event_id: Opaque unique id.
        kind: Event class.
        sender_id: Publishing node identity.
        payload: JSON-serializable body (metrics only).
        timestamp: UTC publish time.
        version: Protocol version stamp.
    """

    event_id: str
    kind: EventKind
    sender_id: str
    payload: dict[str, Any]
    timestamp: datetime
    version: ProtocolVersion

    def __post_init__(self) -> None:
        """Reject empty identity fields."""

        if not self.event_id.strip():
            raise ValueError("event_id must be non-empty")
        if not self.sender_id.strip():
            raise ValueError("sender_id must be non-empty")


def make_event(
    *,
    kind: EventKind,
    sender_id: str,
    payload: dict[str, Any] | None = None,
    event_id: str | None = None,
    timestamp: datetime | None = None,
    version: ProtocolVersion | None = None,
) -> FabricEvent:
    """Construct a FabricEvent with defaults filled in."""

    return FabricEvent(
        event_id=event_id or uuid4().hex,
        kind=kind,
        sender_id=sender_id,
        payload=dict(payload or {}),
        timestamp=timestamp or datetime.now(UTC),
        version=version or FABRIC_PROTOCOL,
    )
