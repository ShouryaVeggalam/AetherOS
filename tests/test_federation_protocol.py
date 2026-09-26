"""Tests for v4.0 P1 Federation Protocol."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from rich.console import Console

from aetheros.federation import (
    PROTOCOL_VERSION,
    FederationPanel,
    FederationRegistry,
    Heartbeat,
    HeartbeatConfig,
    LocalTransport,
    NodeIdentity,
    ProtocolMessage,
    TransportHub,
    build_heartbeat,
    build_snapshot,
    current_version,
    decode_heartbeat,
    decode_message,
    decode_snapshot,
    dumps_canonical,
    encode_heartbeat,
    encode_message,
    encode_snapshot,
    heartbeat_message,
    is_compatible,
    require_compatible,
    seed_demo_federation,
    should_emit,
)
from aetheros.federation.models import FederationSnapshot, NodeRecord
from aetheros.federation.protocol import parse_major_minor
from aetheros.policy_engine.models import TelemetrySnapshot


def _stamp() -> datetime:
    return datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def _node(**kwargs: object) -> NodeIdentity:
    base = {
        "node_id": "node-a",
        "hostname": "host-a",
        "version": "4.0.0",
        "region": "local",
        "created_at": _stamp(),
    }
    base.update(kwargs)
    return NodeIdentity(**base)  # type: ignore[arg-type]


class _Tel:
    def __init__(self) -> None:
        self.cpu_percent = 10.0
        self.memory_percent = 20.0
        self.disk_percent = 30.0
        self.battery_percent = 90.0


# --- models ------------------------------------------------------------------


def test_model_validation() -> None:
    with pytest.raises(ValueError):
        NodeIdentity(
            node_id=" ",
            hostname="h",
            version="1",
            region="r",
            created_at=_stamp(),
        )
    with pytest.raises(ValueError):
        Heartbeat(
            node_id="n",
            cpu=101,
            memory=1,
            disk=1,
            network=1,
            battery=None,
            timestamp=_stamp(),
        )
    with pytest.raises(ValueError):
        FederationSnapshot(
            node=_node(),
            telemetry={"cpu": 1.0},
            context={},
            graph_hash="abc",
            version=PROTOCOL_VERSION,
        )


# --- serialization -----------------------------------------------------------


def test_serialize_heartbeat_roundtrip_deterministic() -> None:
    hb = Heartbeat(
        node_id="n1",
        cpu=11.0,
        memory=22.0,
        disk=33.0,
        network=4.0,
        battery=50.0,
        timestamp=_stamp(),
    )
    raw1 = encode_message(
        ProtocolMessage(
            kind="heartbeat",
            protocol_version=PROTOCOL_VERSION,
            payload=encode_heartbeat(hb),
            sent_at=_stamp(),
            source_node_id="n1",
        )
    )
    # Re-encode decoded message payload path
    msg = decode_message(raw1)
    assert msg.kind == "heartbeat"
    decoded = decode_heartbeat(msg.payload)
    assert decoded.cpu == 11.0
    assert dumps_canonical({"b": 1, "a": 2}) == '{"a":2,"b":1}'
    assert raw1 == encode_message(msg)
    assert raw1 == encode_message(decode_message(raw1))


def test_serialize_snapshot_roundtrip() -> None:
    snap = build_snapshot(
        _node(),
        telemetry={"cpu": 1.0, "memory": 2.0, "disk": 3.0, "network": 0.0},
        context={"intent": "Balanced"},
        graph_hash="deadbeef",
        published_at=_stamp(),
    )
    encoded = encode_snapshot(snap)
    again = decode_snapshot(encoded)
    assert again.graph_hash == "deadbeef"
    assert again.node.node_id == "node-a"


# --- version compatibility ---------------------------------------------------


def test_version_compatibility() -> None:
    assert current_version() == PROTOCOL_VERSION
    assert is_compatible("1.0.0")
    assert is_compatible("1.9.9")
    assert not is_compatible("2.0.0")
    assert not is_compatible("not-a-version")
    assert parse_major_minor("1.2.3") == (1, 2)
    with pytest.raises(ValueError):
        require_compatible("2.0.0")
    with pytest.raises(ValueError):
        parse_major_minor("x")


def test_decode_rejects_incompatible_version() -> None:
    raw = (
        b'{"kind":"heartbeat","payload":{},"protocol_version":"9.0.0",'
        b'"sent_at":"2026-09-26T12:00:00.000000Z","source_node_id":"n"}'
    )
    with pytest.raises(ValueError):
        decode_message(raw)


# --- heartbeat ---------------------------------------------------------------


def test_heartbeat_builder_and_interval() -> None:
    node = _node()
    hb = build_heartbeat(node, _Tel(), network=5.0, now=_stamp())
    assert hb.node_id == node.node_id
    msg = heartbeat_message(node, hb, now=_stamp())
    assert msg.kind == "heartbeat"
    assert should_emit(last_emitted=None, now=_stamp())
    assert not should_emit(
        last_emitted=_stamp(),
        now=_stamp() + timedelta(seconds=1),
        config=HeartbeatConfig(interval_sec=5),
    )
    assert should_emit(
        last_emitted=_stamp(),
        now=_stamp() + timedelta(seconds=6),
        config=HeartbeatConfig(interval_sec=5),
    )
    with pytest.raises(ValueError):
        HeartbeatConfig(interval_sec=0)


# --- registry ----------------------------------------------------------------


def test_registry_online_offline_unknown() -> None:
    reg = FederationRegistry(online_ttl_sec=10)
    node = _node()
    reg.register(node, now=_stamp())
    assert reg.status_of(node.node_id, now=_stamp()) == "unknown"
    hb = build_heartbeat(node, _Tel(), now=_stamp())
    reg.ingest_heartbeat(hb, identity=node, now=_stamp())
    assert reg.status_of(node.node_id, now=_stamp()) == "online"
    # Expire
    later = _stamp() + timedelta(seconds=20)
    assert reg.status_of(node.node_id, now=later) == "offline"
    marked = reg.mark_offline(node.node_id, now=later)
    assert marked is not None and marked.status == "offline"
    assert reg.mark_offline("missing") is None
    view = reg.view(now=later)
    assert view.offline_count >= 1
    assert len(reg) == 1


def test_registry_snapshot_ingest() -> None:
    reg = FederationRegistry()
    snap = build_snapshot(
        _node(),
        telemetry={"cpu": 1.0, "memory": 2.0, "disk": 3.0},
        graph_hash="abc123",
        published_at=_stamp(),
    )
    record = reg.ingest_snapshot(snap, now=_stamp())
    assert record.last_snapshot_hash == "abc123"
    assert record.status == "online"


def test_seed_demo_federation() -> None:
    reg = FederationRegistry(online_ttl_sec=15)
    tel = TelemetrySnapshot(
        timestamp=_stamp(),
        cpu_percent=15,
        memory_percent=25,
        disk_percent=35,
        battery_percent=70,
        process_count=1,
        top_processes=("aetheros",),
    )
    beats, sync = seed_demo_federation(reg, local_telemetry=tel, now=_stamp())
    view = reg.refresh_statuses(now=_stamp())
    assert len(view.nodes) == 3
    assert view.online_count >= 2
    assert view.offline_count >= 1
    assert beats
    assert sync == _stamp()


# --- transport ---------------------------------------------------------------


def test_local_transport_and_hub() -> None:
    bus = LocalTransport(maxsize=8)
    node = _node()
    hb = build_heartbeat(node, _Tel(), now=_stamp())
    msg = heartbeat_message(node, hb, now=_stamp())
    raw = bus.publish(msg)
    assert bus.peek_count() == 1
    drained = bus.drain()
    assert len(drained) == 1
    assert drained[0].source_node_id == "node-a"
    bus.publish_raw(raw)
    bus.clear()
    assert bus.peek_count() == 0

    hub = TransportHub()
    a = hub.register("a")
    hub.register("b")
    assert hub.broadcast(msg, exclude="a") == 1
    assert a.peek_count() == 0
    assert hub.get("b") is not None
    assert len(hub) == 2
    with pytest.raises(ValueError):
        LocalTransport(maxsize=0)


# --- formatter ---------------------------------------------------------------


def test_federation_panel_views() -> None:
    reg = FederationRegistry(online_ttl_sec=15)
    seed_demo_federation(reg, now=_stamp())
    view = reg.refresh_statuses(now=_stamp())
    console = Console(record=True, width=100)
    console.print(FederationPanel())
    assert "idle" in console.export_text().lower() or "FEDERATION" in console.export_text()
    for v in ("nodes", "registry", "heartbeats", "protocol"):
        console = Console(record=True, width=110)
        console.print(
            FederationPanel(
                registry=view,
                heartbeats=tuple(
                    r.last_heartbeat for r in view.nodes if r.last_heartbeat
                ),
                view=v,
                last_sync=_stamp(),
            )
        )
        assert "FEDERATION" in console.export_text()


def test_coverage_edges() -> None:
    with pytest.raises(ValueError):
        ProtocolMessage(
            kind="nope",  # type: ignore[arg-type]
            protocol_version=PROTOCOL_VERSION,
            payload={},
            sent_at=_stamp(),
            source_node_id="n",
        )
    with pytest.raises(ValueError):
        ProtocolMessage(
            kind="heartbeat",
            protocol_version=" ",
            payload={},
            sent_at=_stamp(),
            source_node_id="n",
        )
    with pytest.raises(ValueError):
        ProtocolMessage(
            kind="heartbeat",
            protocol_version=PROTOCOL_VERSION,
            payload={},
            sent_at=_stamp(),
            source_node_id=" ",
        )
    with pytest.raises(ValueError):
        FederationRegistry(online_ttl_sec=0)
    with pytest.raises(ValueError):
        NodeRecord(
            identity=_node(),
            status="weird",  # type: ignore[arg-type]
            last_seen=_stamp(),
        )
    with pytest.raises(ValueError):
        NodeIdentity(
            node_id="n",
            hostname=" ",
            version="1",
            region="r",
            created_at=_stamp(),
        )
    with pytest.raises(ValueError):
        NodeIdentity(
            node_id="n",
            hostname="h",
            version=" ",
            region="r",
            created_at=_stamp(),
        )
    with pytest.raises(ValueError):
        NodeIdentity(
            node_id="n",
            hostname="h",
            version="1",
            region=" ",
            created_at=_stamp(),
        )
    with pytest.raises(ValueError):
        Heartbeat(
            node_id=" ",
            cpu=1,
            memory=1,
            disk=1,
            network=1,
            battery=None,
            timestamp=_stamp(),
        )
    with pytest.raises(ValueError):
        Heartbeat(
            node_id="n",
            cpu=1,
            memory=1,
            disk=1,
            network=1,
            battery=101,
            timestamp=_stamp(),
        )
    with pytest.raises(ValueError):
        Heartbeat(
            node_id="n",
            cpu=1,
            memory=1,
            disk=1,
            network=1,
            battery=None,
            timestamp=_stamp(),
            protocol_version=" ",
        )
    with pytest.raises(ValueError):
        FederationSnapshot(
            node=_node(),
            telemetry={"cpu": 1.0, "memory": 1.0, "disk": 1.0},
            context={},
            graph_hash=" ",
            version=PROTOCOL_VERSION,
        )
    with pytest.raises(ValueError):
        FederationSnapshot(
            node=_node(),
            telemetry={"cpu": 1.0, "memory": 1.0, "disk": 1.0},
            context={},
            graph_hash="x",
            version=" ",
        )
    with pytest.raises(ValueError):
        parse_major_minor("1")
    with pytest.raises(ValueError):
        TransportHub().register(" ")
    # naive datetime encode path
    from aetheros.federation import serializer as ser

    naive = datetime(2026, 9, 26, 12, 0, 0)
    assert ser._dt_to_str(naive).endswith("Z")
    # non-object JSON
    with pytest.raises(ValueError):
        decode_message(b"[1,2,3]")
    # str decode path
    msg = heartbeat_message(_node(), build_heartbeat(_node(), _Tel(), now=_stamp()), now=_stamp())
    text = encode_message(msg).decode("utf-8")
    assert decode_message(text).kind == "heartbeat"
    # hub skip missing recipient
    hub = TransportHub()
    hub.register("a")
    assert hub.publish_to(["missing"], msg) == 0
    # registry degraded when offline > online
    reg = FederationRegistry(online_ttl_sec=5)
    a = _node(node_id="a")
    b = _node(node_id="b", hostname="hb")
    reg.register(a, now=_stamp())
    reg.register(b, now=_stamp())
    reg.ingest_heartbeat(build_heartbeat(a, _Tel(), now=_stamp()), identity=a, now=_stamp())
    reg.mark_offline("a", now=_stamp())
    reg.mark_offline("b", now=_stamp())
    assert reg.view(now=_stamp()).status == "degraded"
    # heartbeat without prior identity
    reg2 = FederationRegistry()
    hb = Heartbeat(
        node_id="orphan",
        cpu=1,
        memory=1,
        disk=1,
        network=1,
        battery=None,
        timestamp=_stamp(),
    )
    rec = reg2.ingest_heartbeat(hb, now=_stamp())
    assert rec.identity.hostname == "orphan"
    empty = FederationRegistry().view()
    assert empty.status == "empty"
    # panel branches: empty registry nodes list vs None already tested;
    # registry with no heartbeats for heartbeats view
    console = Console(record=True, width=80)
    console.print(
        FederationPanel(
            registry=empty,
            heartbeats=(),
            view="heartbeats",
            last_sync=None,
        )
    )
    # empty has no nodes so idle panel — use seeded view without heartbeats param
    seeded = FederationRegistry(online_ttl_sec=15)
    seed_demo_federation(seeded, now=_stamp())
    view = seeded.refresh_statuses(now=_stamp())
    # force records without heartbeat display via empty heartbeats + registry path
    console = Console(record=True, width=100)
    console.print(
        FederationPanel(registry=view, heartbeats=(), view="heartbeats", last_sync=None)
    )
    assert "Heartbeats" in console.export_text() or "FEDERATION" in console.export_text()
