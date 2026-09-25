"""Agent messaging package — structured events, protocol, async bus."""

from aetheros.messaging.bus import AsyncMessageBus
from aetheros.messaging.event import AgentEvent, make_event
from aetheros.messaging.protocol import (
    ALL_AGENT_IDS,
    BROADCAST,
    AgentId,
    EventType,
    decision_payload,
    finding_payload,
)

__all__ = [
    "ALL_AGENT_IDS",
    "BROADCAST",
    "AgentEvent",
    "AgentId",
    "AsyncMessageBus",
    "EventType",
    "decision_payload",
    "finding_payload",
    "make_event",
]
