"""Fabric serialization — JSON-safe encoding of protocol events.

Pure transforms. Never opens sockets.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from aetheros.protocol.events import FabricEvent
from aetheros.protocol.versioning import ProtocolVersion


def event_to_dict(event: FabricEvent) -> dict[str, Any]:
    """Encode a FabricEvent as a JSON-serializable dict."""

    return {
        "event_id": event.event_id,
        "kind": event.kind,
        "sender_id": event.sender_id,
        "payload": dict(event.payload),
        "timestamp": event.timestamp.isoformat(),
        "version": {
            "major": event.version.major,
            "minor": event.version.minor,
            "patch": event.version.patch,
            "label": event.version.label,
        },
    }


def event_from_dict(data: dict[str, Any]) -> FabricEvent:
    """Decode a FabricEvent from a dict (raises on malformed input)."""

    ver = data["version"]
    stamp = datetime.fromisoformat(str(data["timestamp"]))
    return FabricEvent(
        event_id=str(data["event_id"]),
        kind=data["kind"],  # type: ignore[arg-type]
        sender_id=str(data["sender_id"]),
        payload=dict(data.get("payload") or {}),
        timestamp=stamp,
        version=ProtocolVersion(
            int(ver["major"]),
            int(ver["minor"]),
            int(ver["patch"]),
            str(ver.get("label", "aether-fabric")),
        ),
    )


def dumps_event(event: FabricEvent) -> str:
    """Serialize one event to a JSON string."""

    return json.dumps(event_to_dict(event), separators=(",", ":"), sort_keys=True)


def loads_event(raw: str) -> FabricEvent:
    """Deserialize one event from a JSON string."""

    return event_from_dict(json.loads(raw))
