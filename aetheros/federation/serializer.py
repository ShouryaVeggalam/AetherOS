"""Deterministic JSON serializer for Federation Protocol messages.

Versioned schema, sorted keys, ISO-8601 UTC timestamps. No pickle.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from aetheros.federation.models import (
    PROTOCOL_VERSION,
    FederationSnapshot,
    Heartbeat,
    NodeIdentity,
)
from aetheros.federation.protocol import (
    ProtocolMessage,
    require_compatible,
)


def _dt_to_str(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _dt_from_str(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text).astimezone(UTC)


def encode_identity(node: NodeIdentity) -> dict[str, Any]:
    return {
        "node_id": node.node_id,
        "hostname": node.hostname,
        "version": node.version,
        "region": node.region,
        "created_at": _dt_to_str(node.created_at),
    }


def decode_identity(data: dict[str, Any]) -> NodeIdentity:
    return NodeIdentity(
        node_id=str(data["node_id"]),
        hostname=str(data["hostname"]),
        version=str(data["version"]),
        region=str(data["region"]),
        created_at=_dt_from_str(str(data["created_at"])),
    )


def encode_heartbeat(hb: Heartbeat) -> dict[str, Any]:
    return {
        "node_id": hb.node_id,
        "cpu": float(hb.cpu),
        "memory": float(hb.memory),
        "disk": float(hb.disk),
        "network": float(hb.network),
        "battery": None if hb.battery is None else float(hb.battery),
        "timestamp": _dt_to_str(hb.timestamp),
        "protocol_version": hb.protocol_version,
    }


def decode_heartbeat(data: dict[str, Any]) -> Heartbeat:
    require_compatible(str(data.get("protocol_version", PROTOCOL_VERSION)))
    battery_raw = data.get("battery")
    battery = None if battery_raw is None else float(battery_raw)
    return Heartbeat(
        node_id=str(data["node_id"]),
        cpu=float(data["cpu"]),
        memory=float(data["memory"]),
        disk=float(data["disk"]),
        network=float(data["network"]),
        battery=battery,
        timestamp=_dt_from_str(str(data["timestamp"])),
        protocol_version=str(data.get("protocol_version", PROTOCOL_VERSION)),
    )


def encode_snapshot(snap: FederationSnapshot) -> dict[str, Any]:
    telemetry = {k: snap.telemetry[k] for k in sorted(snap.telemetry)}
    context = {k: snap.context[k] for k in sorted(snap.context)}
    body: dict[str, Any] = {
        "node": encode_identity(snap.node),
        "telemetry": telemetry,
        "context": context,
        "graph_hash": snap.graph_hash,
        "version": snap.version,
    }
    if snap.published_at is not None:
        body["published_at"] = _dt_to_str(snap.published_at)
    return body


def decode_snapshot(data: dict[str, Any]) -> FederationSnapshot:
    require_compatible(str(data.get("version", PROTOCOL_VERSION)))
    published = data.get("published_at")
    return FederationSnapshot(
        node=decode_identity(dict(data["node"])),
        telemetry=dict(data["telemetry"]),
        context=dict(data.get("context") or {}),
        graph_hash=str(data["graph_hash"]),
        version=str(data["version"]),
        published_at=_dt_from_str(str(published)) if published else None,
    )


def encode_message(message: ProtocolMessage) -> bytes:
    """Serialize a protocol message to deterministic UTF-8 JSON bytes."""

    envelope = {
        "kind": message.kind,
        "protocol_version": message.protocol_version,
        "source_node_id": message.source_node_id,
        "sent_at": _dt_to_str(message.sent_at),
        "payload": message.payload,
    }
    text = json.dumps(
        envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return text.encode("utf-8")


def decode_message(raw: bytes | str) -> ProtocolMessage:
    """Decode JSON bytes/str into a ``ProtocolMessage``; checks version."""

    if isinstance(raw, bytes):
        text = raw.decode("utf-8")
    else:
        text = raw
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("federation message must be a JSON object")
    version = str(data.get("protocol_version", ""))
    require_compatible(version)
    return ProtocolMessage(
        kind=data["kind"],  # validated in __post_init__
        protocol_version=version,
        payload=dict(data.get("payload") or {}),
        sent_at=_dt_from_str(str(data["sent_at"])),
        source_node_id=str(data["source_node_id"]),
    )


def dumps_canonical(obj: dict[str, Any]) -> str:
    """Canonical JSON string (sorted keys, compact separators)."""

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
