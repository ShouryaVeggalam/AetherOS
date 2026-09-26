"""Federation Protocol — versioned message envelope and compatibility.

Defines the read-only wire contract. Nodes publish heartbeats and snapshots.
Never encodes remote commands, SSH, or control actions.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal

from aetheros.federation.models import PROTOCOL_VERSION

if TYPE_CHECKING:
    from aetheros.federation.models import FederationSnapshot, NodeIdentity

MessageKind = Literal["heartbeat", "snapshot", "announce", "goodbye"]

# Minor versions within the same major are compatible for ingest.
SUPPORTED_MAJORS: frozenset[int] = frozenset({1})


@dataclass(frozen=True, slots=True)
class ProtocolMessage:
    """Versioned envelope wrapping one federation payload."""

    kind: MessageKind
    protocol_version: str
    payload: dict[str, Any]
    sent_at: datetime
    source_node_id: str

    def __post_init__(self) -> None:
        if self.kind not in ("heartbeat", "snapshot", "announce", "goodbye"):
            raise ValueError(f"invalid kind: {self.kind}")
        if not self.protocol_version.strip():
            raise ValueError("protocol_version must be non-empty")
        if not self.source_node_id.strip():
            raise ValueError("source_node_id must be non-empty")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict")


def parse_major_minor(version: str) -> tuple[int, int]:
    """Parse ``major.minor`` or ``major.minor.patch``; raises on garbage."""

    text = version.strip().lstrip("vV")
    parts = text.split(".")
    if len(parts) < 2:
        raise ValueError(f"unsupported version format: {version}")
    try:
        major = int(parts[0])
        minor = int(parts[1])
    except ValueError as exc:
        raise ValueError(f"unsupported version format: {version}") from exc
    return major, minor


def is_compatible(version: str, *, local: str = PROTOCOL_VERSION) -> bool:
    """Return True when ``version`` shares a supported major with ``local``."""

    try:
        remote_major, _ = parse_major_minor(version)
        local_major, _ = parse_major_minor(local)
    except ValueError:
        return False
    if remote_major not in SUPPORTED_MAJORS:
        return False
    return remote_major == local_major


def require_compatible(version: str, *, local: str = PROTOCOL_VERSION) -> None:
    """Raise ``ValueError`` when versions are incompatible."""

    if not is_compatible(version, local=local):
        raise ValueError(
            f"incompatible federation protocol: remote={version} local={local}"
        )


def current_version() -> str:
    """Return the local protocol version string."""

    return PROTOCOL_VERSION


def build_snapshot(
    node: "NodeIdentity",
    *,
    telemetry: Mapping[str, float | None],
    context: Mapping[str, Any] | None = None,
    graph_hash: str,
    version: str | None = None,
    published_at: datetime | None = None,
) -> "FederationSnapshot":
    """Construct an immutable federation snapshot (read-only publish unit)."""

    from aetheros.federation.models import FederationSnapshot

    return FederationSnapshot(
        node=node,
        telemetry=dict(telemetry),
        context=dict(context or {}),
        graph_hash=graph_hash,
        version=version or PROTOCOL_VERSION,
        published_at=published_at,
    )
