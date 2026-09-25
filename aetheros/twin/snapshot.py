"""Digital Twin snapshot engine — create, clone, and restore immutably.

Never mutates the live ResourceGraph. Clones always allocate new containers.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from aetheros.bridge.simulation import clone_graph
from aetheros.graph.models import ResourceGraph
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.twin.models import TwinSnapshot


def create_snapshot(
    resource_graph: ResourceGraph,
    telemetry: TelemetrySnapshot,
    *,
    intent: str | None = None,
    now: datetime | None = None,
    snapshot_id: str | None = None,
) -> TwinSnapshot:
    """Capture an immutable twin snapshot from graph + telemetry.

    The graph is cloned so later scenario runs cannot alias live state.
    """

    stamp = now if now is not None else datetime.now(UTC)
    return TwinSnapshot(
        id=snapshot_id or f"twin:{uuid.uuid4().hex[:12]}",
        timestamp=stamp,
        resource_graph=clone_graph(resource_graph),
        telemetry=telemetry,
        intent=intent,
    )


def clone_snapshot(
    snapshot: TwinSnapshot,
    *,
    now: datetime | None = None,
    snapshot_id: str | None = None,
) -> TwinSnapshot:
    """Deep-clone a TwinSnapshot (new id, cloned graph, copied telemetry)."""

    stamp = now if now is not None else datetime.now(UTC)
    tel = snapshot.telemetry
    telemetry = TelemetrySnapshot(
        timestamp=tel.timestamp,
        cpu_percent=tel.cpu_percent,
        memory_percent=tel.memory_percent,
        disk_percent=tel.disk_percent,
        battery_percent=tel.battery_percent,
        process_count=tel.process_count,
        top_processes=tuple(tel.top_processes),
    )
    return TwinSnapshot(
        id=snapshot_id or f"twin:{uuid.uuid4().hex[:12]}",
        timestamp=stamp,
        resource_graph=clone_graph(snapshot.resource_graph),
        telemetry=telemetry,
        intent=snapshot.intent,
    )


def restore_snapshot(snapshot: TwinSnapshot) -> TwinSnapshot:
    """Return a fresh clone suitable for replaying scenarios from baseline.

    Does not resurrect live system state — restores the twin sandbox only.
    """

    return clone_snapshot(snapshot)
