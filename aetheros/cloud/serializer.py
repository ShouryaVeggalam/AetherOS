"""JSON serializer for cloud federation snapshots (no pickle)."""

from __future__ import annotations

import json
from typing import Any

from aetheros.cloud.models import InfrastructureSnapshot


def dumps_canonical(payload: dict[str, Any]) -> str:
    """Encode a mapping as canonical UTF-8 JSON (sorted keys)."""

    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def encode_snapshot(snapshot: InfrastructureSnapshot) -> str:
    """Serialize an InfrastructureSnapshot to canonical JSON text."""

    return dumps_canonical(snapshot.to_dict())


def decode_snapshot(text: str) -> InfrastructureSnapshot:
    """Parse an InfrastructureSnapshot from JSON text."""

    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("snapshot JSON must be an object")
    return InfrastructureSnapshot.from_dict(data)


def snapshot_to_json(
    snapshot: InfrastructureSnapshot, *, indent: int | None = 2
) -> str:
    """Pretty or compact JSON export for operators."""

    if indent is None:
        return encode_snapshot(snapshot)
    return json.dumps(
        snapshot.to_dict(),
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
    )
