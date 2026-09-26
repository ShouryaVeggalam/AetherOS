"""Federation registry — tracks online/offline/unknown nodes.

Append-ingest of heartbeats and snapshots. Never stores private user data.
Never executes remote actions. Status derived from last_seen + TTL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from aetheros.federation.models import (
    PROTOCOL_VERSION,
    FederationSnapshot,
    Heartbeat,
    NodeIdentity,
    NodeRecord,
    NodeStatus,
    RegistryView,
)
from aetheros.federation.protocol import require_compatible

DEFAULT_ONLINE_TTL_SEC = 15.0


@dataclass
class FederationRegistry:
    """In-memory registry of federation nodes (read-only observation).

    Mutable container; records themselves remain frozen. No shared mutable
    cross-node state beyond last-seen observation.
    """

    online_ttl_sec: float = DEFAULT_ONLINE_TTL_SEC
    _nodes: dict[str, NodeRecord] = field(default_factory=dict)
    _identities: dict[str, NodeIdentity] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.online_ttl_sec <= 0:
            raise ValueError("online_ttl_sec must be > 0")

    def register(self, identity: NodeIdentity, *, now: datetime | None = None) -> NodeRecord:
        """Announce a node identity (status unknown until heartbeat)."""

        stamp = now or datetime.now(UTC)
        self._identities[identity.node_id] = identity
        existing = self._nodes.get(identity.node_id)
        record = NodeRecord(
            identity=identity,
            status=existing.status if existing else "unknown",
            last_seen=existing.last_seen if existing else stamp,
            last_heartbeat=existing.last_heartbeat if existing else None,
            last_snapshot_hash=existing.last_snapshot_hash if existing else "",
        )
        self._nodes[identity.node_id] = record
        return record

    def ingest_heartbeat(
        self,
        heartbeat: Heartbeat,
        *,
        identity: NodeIdentity | None = None,
        now: datetime | None = None,
    ) -> NodeRecord:
        """Ingest a heartbeat and mark the node online."""

        require_compatible(heartbeat.protocol_version)
        stamp = now or heartbeat.timestamp
        ident = identity or self._identities.get(heartbeat.node_id)
        if ident is None:
            ident = NodeIdentity(
                node_id=heartbeat.node_id,
                hostname=heartbeat.node_id,
                version="unknown",
                region="unknown",
                created_at=stamp,
            )
        self._identities[heartbeat.node_id] = ident
        record = NodeRecord(
            identity=ident,
            status="online",
            last_seen=stamp,
            last_heartbeat=heartbeat,
            last_snapshot_hash=self._nodes.get(
                heartbeat.node_id, NodeRecord(ident, "unknown", stamp)
            ).last_snapshot_hash,
        )
        self._nodes[heartbeat.node_id] = record
        return record

    def ingest_snapshot(
        self,
        snapshot: FederationSnapshot,
        *,
        now: datetime | None = None,
    ) -> NodeRecord:
        """Ingest an immutable snapshot; updates last_seen and graph hash."""

        require_compatible(snapshot.version)
        stamp = now or snapshot.published_at or datetime.now(UTC)
        self._identities[snapshot.node.node_id] = snapshot.node
        prev = self._nodes.get(snapshot.node.node_id)
        record = NodeRecord(
            identity=snapshot.node,
            status="online",
            last_seen=stamp,
            last_heartbeat=prev.last_heartbeat if prev else None,
            last_snapshot_hash=snapshot.graph_hash,
        )
        self._nodes[snapshot.node.node_id] = record
        return record

    def mark_offline(self, node_id: str, *, now: datetime | None = None) -> NodeRecord | None:
        """Explicit goodbye / offline mark."""

        prev = self._nodes.get(node_id)
        if prev is None:
            return None
        stamp = now or datetime.now(UTC)
        record = NodeRecord(
            identity=prev.identity,
            status="offline",
            last_seen=stamp,
            last_heartbeat=prev.last_heartbeat,
            last_snapshot_hash=prev.last_snapshot_hash,
        )
        self._nodes[node_id] = record
        return record

    def refresh_statuses(self, *, now: datetime | None = None) -> RegistryView:
        """Recompute online/offline from TTL; return immutable view."""

        stamp = now or datetime.now(UTC)
        ttl = timedelta(seconds=self.online_ttl_sec)
        updated: dict[str, NodeRecord] = {}
        for node_id, record in self._nodes.items():
            status: NodeStatus = record.status
            if record.status == "online" and stamp - record.last_seen > ttl:
                status = "offline"
            elif record.status == "unknown":
                status = "unknown"
            if status != record.status:
                record = NodeRecord(
                    identity=record.identity,
                    status=status,
                    last_seen=record.last_seen,
                    last_heartbeat=record.last_heartbeat,
                    last_snapshot_hash=record.last_snapshot_hash,
                )
            updated[node_id] = record
        self._nodes = updated
        return self.view(now=stamp)

    def status_of(self, node_id: str, *, now: datetime | None = None) -> NodeStatus:
        """Return current status for a node (applies TTL)."""

        view = self.refresh_statuses(now=now)
        for record in view.nodes:
            if record.identity.node_id == node_id:
                return record.status
        return "unknown"

    def view(self, *, now: datetime | None = None) -> RegistryView:
        """Immutable aggregate registry view."""

        nodes = tuple(
            sorted(self._nodes.values(), key=lambda r: r.identity.node_id)
        )
        online = sum(1 for n in nodes if n.status == "online")
        offline = sum(1 for n in nodes if n.status == "offline")
        unknown = sum(1 for n in nodes if n.status == "unknown")
        last_seen = max((n.last_seen for n in nodes), default=None)
        if not nodes:
            health = "empty"
        elif offline > online:
            health = "degraded"
        else:
            health = "healthy"
        return RegistryView(
            nodes=nodes,
            last_seen=last_seen,
            status=health,
            protocol_version=PROTOCOL_VERSION,
            online_count=online,
            offline_count=offline,
            unknown_count=unknown,
        )

    def __len__(self) -> int:
        return len(self._nodes)
