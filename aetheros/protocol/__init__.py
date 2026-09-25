"""Aether Fabric protocol — events, transport, serialization, versioning."""

from aetheros.protocol.events import EventKind, FabricEvent, make_event
from aetheros.protocol.serialization import (
    dumps_event,
    event_from_dict,
    event_to_dict,
    loads_event,
)
from aetheros.protocol.transport import InProcessTransport
from aetheros.protocol.versioning import FABRIC_PROTOCOL, ProtocolVersion

__all__ = [
    "FABRIC_PROTOCOL",
    "EventKind",
    "FabricEvent",
    "InProcessTransport",
    "ProtocolVersion",
    "dumps_event",
    "event_from_dict",
    "event_to_dict",
    "loads_event",
    "make_event",
]
