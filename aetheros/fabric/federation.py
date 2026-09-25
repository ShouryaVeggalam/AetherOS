"""Federation — immutable telemetry snapshot exchange.

Every node publishes CPU/Memory/GPU/Network/Health/Timestamp/Version.
Eventual consistency via in-process transport. Never executes remote actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from aetheros.fabric.identity import SEED_IDENTITIES, FabricIdentity
from aetheros.protocol import InProcessTransport, make_event
from aetheros.protocol.versioning import FABRIC_PROTOCOL


@dataclass(frozen=True, slots=True)
class FederatedSnapshot:
    """One immutable federated telemetry snapshot.

    Attributes:
        node_id: Publisher identity.
        cpu: CPU percent 0–100.
        memory: Memory percent 0–100.
        gpu: GPU percent 0–100 (0 if absent).
        network: Network health proxy 0–100.
        health: Node health 0–100.
        timestamp: UTC sample time.
        version: Fabric version string.
    """

    node_id: str
    cpu: float
    memory: float
    gpu: float
    network: float
    health: float
    timestamp: datetime
    version: str

    def __post_init__(self) -> None:
        """Validate metric ranges."""

        for name in ("cpu", "memory", "gpu", "network", "health"):
            value = getattr(self, name)
            if not 0.0 <= float(value) <= 100.0:
                raise ValueError(f"{name} must be in [0, 100]")


@dataclass(frozen=True, slots=True)
class FederationHealth:
    """Aggregate federation health view."""

    member_count: int
    synced_count: int
    synchronization: float
    mean_health: float
    stale_nodes: tuple[str, ...]


@dataclass
class Federation:
    """Federation registry of identities and latest snapshots."""

    transport: InProcessTransport = field(default_factory=InProcessTransport)
    identities: tuple[FabricIdentity, ...] = field(
        default_factory=lambda: SEED_IDENTITIES
    )
    _latest: dict[str, FederatedSnapshot] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        """Subscribe all seed identities and publish baseline snapshots."""

        for identity in self.identities:
            self.transport.subscribe(identity.node_id)
            self.publish(
                FederatedSnapshot(
                    node_id=identity.node_id,
                    cpu=35.0 + (hash(identity.node_id) % 30),
                    memory=40.0 + (hash(identity.node_id[::-1]) % 25),
                    gpu=20.0 if identity.node_class == "ai_cluster" else 0.0,
                    network=92.0,
                    health=96.0 + (hash(identity.node_id) % 4),
                    timestamp=datetime.now(UTC),
                    version=identity.version,
                )
            )

    def publish(self, snapshot: FederatedSnapshot) -> None:
        """Store and broadcast one immutable snapshot (read-only federation)."""

        self._latest[snapshot.node_id] = snapshot
        self.transport.publish(
            make_event(
                kind="telemetry.snapshot",
                sender_id=snapshot.node_id,
                payload={
                    "cpu": snapshot.cpu,
                    "memory": snapshot.memory,
                    "gpu": snapshot.gpu,
                    "network": snapshot.network,
                    "health": snapshot.health,
                    "version": snapshot.version,
                    "protocol": str(FABRIC_PROTOCOL),
                },
                timestamp=snapshot.timestamp,
            )
        )

    def snapshots(self) -> tuple[FederatedSnapshot, ...]:
        """Latest snapshot per known node."""

        return tuple(self._latest.values())

    def health(self) -> FederationHealth:
        """Compute federation synchronization / health summary."""

        snaps = self.snapshots()
        if not snaps:
            return FederationHealth(0, 0, 0.0, 0.0, ())
        now = datetime.now(UTC)
        stale: list[str] = []
        synced = 0
        for snap in snaps:
            age = (now - snap.timestamp).total_seconds()
            if age <= 120.0:
                synced += 1
            else:
                stale.append(snap.node_id)
        sync_pct = (synced / len(snaps)) * 100.0
        mean_health = sum(s.health for s in snaps) / len(snaps)
        return FederationHealth(
            member_count=len(snaps),
            synced_count=synced,
            synchronization=round(sync_pct, 2),
            mean_health=round(mean_health, 2),
            stale_nodes=tuple(stale),
        )
