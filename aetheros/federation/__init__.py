"""Federation Protocol — v4.0 P1 read-only multi-node snapshot exchange.

Nodes publish immutable telemetry snapshots and heartbeats. Never SSH.
Never remote execution. Never mutable shared control state.
"""

from __future__ import annotations

from aetheros.federation.demo import seed_demo_federation
from aetheros.federation.formatter import FederationPanel
from aetheros.federation.heartbeat import (
    DEFAULT_HEARTBEAT_INTERVAL_SEC,
    HeartbeatConfig,
    build_heartbeat,
    heartbeat_message,
    should_emit,
)
from aetheros.federation.models import (
    PROTOCOL_VERSION,
    FederationSnapshot,
    Heartbeat,
    NodeIdentity,
    NodeRecord,
    NodeStatus,
    RegistryView,
)
from aetheros.federation.protocol import (
    ProtocolMessage,
    build_snapshot,
    current_version,
    is_compatible,
    require_compatible,
)
from aetheros.federation.registry import DEFAULT_ONLINE_TTL_SEC, FederationRegistry
from aetheros.federation.serializer import (
    decode_heartbeat,
    decode_message,
    decode_snapshot,
    dumps_canonical,
    encode_heartbeat,
    encode_message,
    encode_snapshot,
)
from aetheros.federation.transport import LocalTransport, TransportHub

__all__ = [
    "DEFAULT_HEARTBEAT_INTERVAL_SEC",
    "DEFAULT_ONLINE_TTL_SEC",
    "FederationPanel",
    "FederationRegistry",
    "FederationSnapshot",
    "Heartbeat",
    "HeartbeatConfig",
    "LocalTransport",
    "NodeIdentity",
    "NodeRecord",
    "NodeStatus",
    "PROTOCOL_VERSION",
    "ProtocolMessage",
    "RegistryView",
    "TransportHub",
    "build_heartbeat",
    "build_snapshot",
    "current_version",
    "decode_heartbeat",
    "decode_message",
    "decode_snapshot",
    "dumps_canonical",
    "encode_heartbeat",
    "encode_message",
    "encode_snapshot",
    "heartbeat_message",
    "is_compatible",
    "require_compatible",
    "seed_demo_federation",
    "should_emit",
]
