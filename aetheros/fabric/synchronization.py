"""Fabric synchronization — eventual-consistency reconciliation.

Merges federated snapshots by newest timestamp. Never pushes commands.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aetheros.fabric.federation import FederatedSnapshot, Federation
from aetheros.protocol import InProcessTransport


@dataclass(frozen=True, slots=True)
class SyncReport:
    """Immutable synchronization cycle result."""

    events_processed: int
    nodes_updated: int
    synchronization: float
    notes: tuple[str, ...]


@dataclass
class Synchronizer:
    """Reconcile federation mailboxes into a consistent local view."""

    federation: Federation
    transport: InProcessTransport | None = None
    _local_view: dict[str, FederatedSnapshot] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        """Bind transport default and seed local view."""

        if self.transport is None:
            self.transport = self.federation.transport
        for snap in self.federation.snapshots():
            self._local_view[snap.node_id] = snap

    def tick(self, *, observer_id: str = "node.local.pc") -> SyncReport:
        """Drain events for ``observer_id`` and merge by newest timestamp."""

        assert self.transport is not None
        events = self.transport.drain(observer_id)
        updated = 0
        notes: list[str] = []
        for event in events:
            if event.kind != "telemetry.snapshot":
                continue
            payload = event.payload
            candidate = FederatedSnapshot(
                node_id=event.sender_id,
                cpu=float(payload.get("cpu", 0.0)),
                memory=float(payload.get("memory", 0.0)),
                gpu=float(payload.get("gpu", 0.0)),
                network=float(payload.get("network", 0.0)),
                health=float(payload.get("health", 0.0)),
                timestamp=event.timestamp,
                version=str(payload.get("version", "unknown")),
            )
            existing = self._local_view.get(candidate.node_id)
            if existing is None or candidate.timestamp >= existing.timestamp:
                self._local_view[candidate.node_id] = candidate
                updated += 1
        health = self.federation.health()
        if not events:
            notes.append("No pending events — view already consistent.")
        else:
            notes.append(
                f"Merged {len(events)} events with eventual-consistency (newest wins)."
            )
        notes.append("No remote actions executed.")
        return SyncReport(
            events_processed=len(events),
            nodes_updated=updated,
            synchronization=health.synchronization,
            notes=tuple(notes),
        )

    def view(self) -> tuple[FederatedSnapshot, ...]:
        """Current reconciled local view."""

        return tuple(self._local_view.values())
