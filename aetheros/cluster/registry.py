"""Cluster node registry — ingest transport messages and persist nodes.

SQLite append/upsert of latest node state. Never runs remote commands.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from aetheros.cluster.heartbeat import HeartbeatTracker
from aetheros.cluster.models import ClusterNode
from aetheros.cluster.node import node_from_payload, node_to_payload
from aetheros.cluster.transport import ClusterTransport, TransportMessage

_CREATE = """
CREATE TABLE IF NOT EXISTS cluster_nodes (
    node_id TEXT PRIMARY KEY,
    hostname TEXT NOT NULL,
    platform TEXT NOT NULL,
    cpu REAL NOT NULL,
    memory REAL NOT NULL,
    disk REAL NOT NULL,
    battery REAL,
    latency REAL NOT NULL,
    last_seen TEXT NOT NULL
);
"""

_UPSERT = """
INSERT INTO cluster_nodes
    (node_id, hostname, platform, cpu, memory, disk, battery, latency, last_seen)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(node_id) DO UPDATE SET
    hostname=excluded.hostname,
    platform=excluded.platform,
    cpu=excluded.cpu,
    memory=excluded.memory,
    disk=excluded.disk,
    battery=excluded.battery,
    latency=excluded.latency,
    last_seen=excluded.last_seen;
"""


@dataclass
class NodeRegistry:
    """Track cluster members from local transport messages.

    Args:
        transport: Publish/subscribe bus.
        db_path: SQLite path for latest node snapshots.
        heartbeats: Liveness tracker.
    """

    transport: ClusterTransport
    db_path: Path = field(default_factory=lambda: Path("data/cluster.db"))
    heartbeats: HeartbeatTracker = field(default_factory=HeartbeatTracker)
    _nodes: dict[str, ClusterNode] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        """Create tables and load any persisted nodes."""

        self.db_path = Path(self.db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_CREATE)
            conn.commit()
        self._load_from_db()

    def ingest(self, *, max_messages: int = 100) -> int:
        """Drain transport messages and update registry state.

        Returns:
            Number of messages processed.
        """

        messages = self.transport.subscribe(max_messages=max_messages)
        for message in messages:
            self._apply_message(message)
        return len(messages)

    def upsert(self, node: ClusterNode) -> None:
        """Insert or replace one node snapshot and mark it seen."""

        self._nodes[node.node_id] = node
        self.heartbeats.record_seen(node.node_id, node.last_seen, online=True)
        self._persist(node)

    def get(self, node_id: str) -> ClusterNode | None:
        """Return one node by id, if known."""

        return self._nodes.get(node_id)

    def nodes(self) -> tuple[ClusterNode, ...]:
        """Return all known nodes sorted by hostname."""

        return tuple(sorted(self._nodes.values(), key=lambda n: n.hostname.lower()))

    def is_online(self, node_id: str) -> bool:
        """Delegate online checks to the heartbeat tracker."""

        return self.heartbeats.is_online(node_id)

    def _apply_message(self, message: TransportMessage) -> None:
        """Apply one telemetry or heartbeat message."""

        if message.kind == "telemetry":
            node = node_from_payload(message.payload)
            self.upsert(node)
            return
        beat = self.heartbeats.heartbeat_from_message(message)
        if beat is not None:
            self.heartbeats.record(beat)

    def _persist(self, node: ClusterNode) -> None:
        """Upsert the latest node row into SQLite."""

        payload = node_to_payload(node)
        with self._connect() as conn:
            conn.execute(
                _UPSERT,
                (
                    payload["node_id"],
                    payload["hostname"],
                    payload["platform"],
                    payload["cpu"],
                    payload["memory"],
                    payload["disk"],
                    payload["battery"],
                    payload["latency"],
                    payload["last_seen"],
                ),
            )
            conn.commit()

    def _load_from_db(self) -> None:
        """Hydrate in-memory nodes from SQLite (may be stale/offline)."""

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT node_id, hostname, platform, cpu, memory, disk, "
                "battery, latency, last_seen FROM cluster_nodes"
            ).fetchall()
        for row in rows:
            payload = {
                "node_id": row[0],
                "hostname": row[1],
                "platform": row[2],
                "cpu": row[3],
                "memory": row[4],
                "disk": row[5],
                "battery": row[6],
                "latency": row[7],
                "last_seen": row[8],
            }
            node = node_from_payload(payload)
            self._nodes[node.node_id] = node
            # Do not mark as online — last_seen may be stale after restart.

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection."""

        return sqlite3.connect(self.db_path)
