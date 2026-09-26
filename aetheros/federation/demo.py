"""Demo seeding for Federation Protocol dashboard (local + synthetic peers).

Read-only. Never opens SSH. Never executes remote commands.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha1

from aetheros.federation.heartbeat import build_heartbeat, heartbeat_message
from aetheros.federation.models import PROTOCOL_VERSION, Heartbeat, NodeIdentity
from aetheros.federation.protocol import ProtocolMessage, build_snapshot
from aetheros.federation.registry import FederationRegistry
from aetheros.federation.serializer import encode_snapshot
from aetheros.federation.transport import LocalTransport, TransportHub
from aetheros.policy_engine.models import TelemetrySnapshot


class _Tel:
    __slots__ = ("cpu_percent", "memory_percent", "disk_percent", "battery_percent")

    def __init__(
        self,
        cpu: float,
        memory: float,
        disk: float,
        battery: float | None,
    ) -> None:
        self.cpu_percent = cpu
        self.memory_percent = memory
        self.disk_percent = disk
        self.battery_percent = battery


def seed_demo_federation(
    registry: FederationRegistry,
    *,
    local_telemetry: TelemetrySnapshot | None = None,
    now: datetime | None = None,
) -> tuple[tuple[Heartbeat, ...], datetime]:
    """Populate registry with local node + two demo peers (one offline)."""

    stamp = now or datetime.now(UTC)
    hub = TransportHub()
    local_bus = hub.register("node-local")
    peer_bus = hub.register("node-peer-a")

    local = NodeIdentity(
        node_id="node-local",
        hostname="aetheros-local",
        version="4.0.0",
        region="local",
        created_at=stamp - timedelta(days=1),
    )
    peer_a = NodeIdentity(
        node_id="node-peer-a",
        hostname="aetheros-peer-a",
        version="4.0.0",
        region="us-west",
        created_at=stamp - timedelta(hours=6),
    )
    peer_b = NodeIdentity(
        node_id="node-peer-b",
        hostname="aetheros-peer-b",
        version="3.9.0",
        region="eu-central",
        created_at=stamp - timedelta(hours=12),
    )

    registry.register(local, now=stamp)
    registry.register(peer_a, now=stamp)
    registry.register(peer_b, now=stamp - timedelta(seconds=60))

    if local_telemetry is not None:
        tel = _Tel(
            local_telemetry.cpu_percent,
            local_telemetry.memory_percent,
            local_telemetry.disk_percent,
            local_telemetry.battery_percent,
        )
    else:
        tel = _Tel(22.0, 41.0, 55.0, 80.0)

    hb_local = build_heartbeat(local, tel, network=12.0, now=stamp)
    registry.ingest_heartbeat(hb_local, identity=local, now=stamp)
    msg = heartbeat_message(local, hb_local, now=stamp)
    local_bus.publish(msg)
    hub.broadcast(msg, exclude=local.node_id)

    hb_peer = build_heartbeat(
        peer_a, _Tel(35.0, 50.0, 40.0, None), network=28.0, now=stamp
    )
    registry.ingest_heartbeat(hb_peer, identity=peer_a, now=stamp)
    peer_msg = heartbeat_message(peer_a, hb_peer, now=stamp)
    peer_bus.publish(peer_msg)

    # Offline peer: stale heartbeat beyond TTL.
    stale = stamp - timedelta(seconds=registry.online_ttl_sec + 5)
    hb_stale = Heartbeat(
        node_id=peer_b.node_id,
        cpu=10.0,
        memory=20.0,
        disk=30.0,
        network=5.0,
        battery=50.0,
        timestamp=stale,
        protocol_version=PROTOCOL_VERSION,
    )
    registry.ingest_heartbeat(hb_stale, identity=peer_b, now=stale)

    graph_hash = sha1(b"local-graph", usedforsecurity=False).hexdigest()[:16]
    snap = build_snapshot(
        local,
        telemetry={
            "cpu": tel.cpu_percent,
            "memory": tel.memory_percent,
            "disk": tel.disk_percent,
            "network": 12.0,
            "battery": tel.battery_percent,
        },
        context={"intent": "Balanced"},
        graph_hash=graph_hash,
        published_at=stamp,
    )
    registry.ingest_snapshot(snap, now=stamp)
    snap_msg = ProtocolMessage(
        kind="snapshot",
        protocol_version=PROTOCOL_VERSION,
        payload=encode_snapshot(snap),
        sent_at=stamp,
        source_node_id=local.node_id,
    )
    hub.broadcast(snap_msg, exclude=local.node_id)

    # Drain peer inbox so transport path is exercised (observational only).
    _ = peer_bus.drain()
    _ = LocalTransport()  # ensure import used for type surface in demos

    view = registry.refresh_statuses(now=stamp)
    beats = tuple(r.last_heartbeat for r in view.nodes if r.last_heartbeat is not None)
    return beats, stamp
