"""Resource Graph builder — construct graphs from live telemetry only.

Never invents GPU, network, cluster, simulation, or research nodes unless
callers supply real optional context. No fake measurements.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aetheros.graph.models import ResourceEdge, ResourceGraph, ResourceNode
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.telemetry.models import SystemSnapshot


def build_resource_graph(
    snapshot: SystemSnapshot | TelemetrySnapshot,
    *,
    intent_name: str | None = None,
    now: datetime | None = None,
) -> ResourceGraph:
    """Build an immutable resource graph from one telemetry sample.

    Args:
        snapshot: ``SystemSnapshot`` (preferred) or flat ``TelemetrySnapshot``.
        intent_name: Optional active intent profile name (real operator state).
        now: Optional clock override for deterministic tests.

    Returns:
        A ``ResourceGraph`` containing only nodes backed by provided data.
    """

    stamp = now if now is not None else datetime.now(UTC)
    if isinstance(snapshot, SystemSnapshot):
        return _from_system(snapshot, intent_name=intent_name, stamp=stamp)
    return _from_telemetry(snapshot, intent_name=intent_name, stamp=stamp)


def _from_system(
    snapshot: SystemSnapshot,
    *,
    intent_name: str | None,
    stamp: datetime,
) -> ResourceGraph:
    """Build from a rich SystemSnapshot (per-core CPU, PIDs, mounts)."""

    nodes: list[ResourceNode] = []
    edges: list[ResourceEdge] = []

    cpu = ResourceNode(
        id="cpu",
        type="CPU",
        name="CPU",
        metadata=(
            ("percent", f"{snapshot.cpu.percent:.1f}"),
            ("cores", str(len(snapshot.cpu.per_cpu_percent))),
            ("load_1", f"{snapshot.cpu.load_avg[0]:.2f}"),
        ),
        created_at=stamp,
    )
    nodes.append(cpu)
    for index, core_pct in enumerate(snapshot.cpu.per_cpu_percent):
        core_id = f"cpu:core:{index}"
        nodes.append(
            ResourceNode(
                id=core_id,
                type="CPU",
                name=f"Core {index}",
                metadata=(("percent", f"{core_pct:.1f}"),),
                created_at=stamp,
            )
        )
        edges.append(
            ResourceEdge(
                source="cpu",
                target=core_id,
                relationship="ALLOCATES",
                weight=_clamp01(core_pct / 100.0),
            )
        )

    nodes.append(
        ResourceNode(
            id="memory",
            type="Memory",
            name="Memory",
            metadata=(
                ("percent", f"{snapshot.memory.percent:.1f}"),
                ("used_bytes", str(snapshot.memory.used_bytes)),
                ("total_bytes", str(snapshot.memory.total_bytes)),
            ),
            created_at=stamp,
        )
    )
    edges.append(
        ResourceEdge(
            source="cpu",
            target="memory",
            relationship="DEPENDS_ON",
            weight=0.5,
        )
    )

    for disk in snapshot.disks:
        disk_id = f"disk:{_slug(disk.mountpoint)}"
        nodes.append(
            ResourceNode(
                id=disk_id,
                type="Disk",
                name=f"Disk {disk.mountpoint}",
                metadata=(
                    ("mountpoint", disk.mountpoint),
                    ("percent", f"{disk.percent:.1f}"),
                    ("used_bytes", str(disk.used_bytes)),
                ),
                created_at=stamp,
            )
        )
        edges.append(
            ResourceEdge(
                source="memory",
                target=disk_id,
                relationship="DEPENDS_ON",
                weight=_clamp01(disk.percent / 100.0),
            )
        )

    if snapshot.battery is not None:
        nodes.append(
            ResourceNode(
                id="battery",
                type="Battery",
                name="Battery",
                metadata=(
                    ("percent", f"{snapshot.battery.percent:.1f}"),
                    (
                        "plugged_in",
                        "true" if snapshot.battery.is_plugged_in else "false",
                    ),
                ),
                created_at=stamp,
            )
        )
        edges.append(
            ResourceEdge(
                source="cpu",
                target="battery",
                relationship="DEPENDS_ON",
                weight=_clamp01(1.0 - snapshot.battery.percent / 100.0),
            )
        )

    primary_disk = (
        f"disk:{_slug(snapshot.disks[0].mountpoint)}" if snapshot.disks else None
    )
    for proc in snapshot.processes:
        proc_id = f"process:{proc.pid}"
        nodes.append(
            ResourceNode(
                id=proc_id,
                type="Process",
                name=proc.name,
                metadata=(
                    ("pid", str(proc.pid)),
                    ("cpu_percent", f"{proc.cpu_percent:.1f}"),
                    ("memory_percent", f"{proc.memory_percent:.1f}"),
                    ("status", proc.status),
                ),
                created_at=stamp,
            )
        )
        edges.append(
            ResourceEdge(
                source=proc_id,
                target="cpu",
                relationship="USES",
                weight=_clamp01(proc.cpu_percent / 100.0),
            )
        )
        edges.append(
            ResourceEdge(
                source=proc_id,
                target="memory",
                relationship="ALLOCATES",
                weight=_clamp01(proc.memory_percent / 100.0),
            )
        )
        if primary_disk is not None:
            edges.append(
                ResourceEdge(
                    source=proc_id,
                    target=primary_disk,
                    relationship="DEPENDS_ON",
                    weight=0.2,
                )
            )

    _append_intent(nodes, edges, intent_name=intent_name, stamp=stamp)
    return ResourceGraph(nodes=tuple(nodes), edges=tuple(edges))


def _from_telemetry(
    snapshot: TelemetrySnapshot,
    *,
    intent_name: str | None,
    stamp: datetime,
) -> ResourceGraph:
    """Build from a flat TelemetrySnapshot (names only for processes)."""

    nodes: list[ResourceNode] = [
        ResourceNode(
            id="cpu",
            type="CPU",
            name="CPU",
            metadata=(("percent", f"{snapshot.cpu_percent:.1f}"),),
            created_at=stamp,
        ),
        ResourceNode(
            id="memory",
            type="Memory",
            name="Memory",
            metadata=(("percent", f"{snapshot.memory_percent:.1f}"),),
            created_at=stamp,
        ),
        ResourceNode(
            id="disk",
            type="Disk",
            name="Disk",
            metadata=(("percent", f"{snapshot.disk_percent:.1f}"),),
            created_at=stamp,
        ),
    ]
    edges: list[ResourceEdge] = [
        ResourceEdge("cpu", "memory", "DEPENDS_ON", 0.5),
        ResourceEdge(
            "memory",
            "disk",
            "DEPENDS_ON",
            _clamp01(snapshot.disk_percent / 100.0),
        ),
    ]
    if snapshot.battery_percent is not None:
        nodes.append(
            ResourceNode(
                id="battery",
                type="Battery",
                name="Battery",
                metadata=(("percent", f"{snapshot.battery_percent:.1f}"),),
                created_at=stamp,
            )
        )
        edges.append(
            ResourceEdge(
                "cpu",
                "battery",
                "DEPENDS_ON",
                _clamp01(1.0 - snapshot.battery_percent / 100.0),
            )
        )
    for index, name in enumerate(snapshot.top_processes):
        proc_id = f"process:rank:{index}:{_slug(name)}"
        nodes.append(
            ResourceNode(
                id=proc_id,
                type="Process",
                name=name,
                metadata=(("rank", str(index)),),
                created_at=stamp,
            )
        )
        edges.append(ResourceEdge(proc_id, "cpu", "USES", 0.5))
        edges.append(ResourceEdge(proc_id, "memory", "ALLOCATES", 0.4))
        edges.append(ResourceEdge(proc_id, "disk", "DEPENDS_ON", 0.2))
    _append_intent(nodes, edges, intent_name=intent_name, stamp=stamp)
    return ResourceGraph(nodes=tuple(nodes), edges=tuple(edges))


def _append_intent(
    nodes: list[ResourceNode],
    edges: list[ResourceEdge],
    *,
    intent_name: str | None,
    stamp: datetime,
) -> None:
    """Attach a real intent node when an operator profile name is provided."""

    if intent_name is None or not intent_name.strip():
        return
    nodes.append(
        ResourceNode(
            id="intent:active",
            type="Intent",
            name=intent_name.strip(),
            metadata=(("profile", intent_name.strip()),),
            created_at=stamp,
        )
    )
    edges.append(ResourceEdge("intent:active", "cpu", "PREDICTS", 0.3))


def _slug(value: str) -> str:
    """Filesystem-/id-safe slug from a path or process name."""

    cleaned = "".join(ch if ch.isalnum() else "_" for ch in value.strip())
    return cleaned.strip("_") or "root"


def _clamp01(value: float) -> float:
    """Clamp a float into [0, 1]."""

    return max(0.0, min(1.0, float(value)))
