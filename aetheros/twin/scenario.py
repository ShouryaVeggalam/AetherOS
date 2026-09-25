"""Digital Twin scenario engine — built-in what-ifs on cloned snapshots only."""

from __future__ import annotations

from datetime import UTC, datetime

from aetheros.graph.models import ResourceGraph, ResourceNode
from aetheros.graph.queries import nodes_of_type
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.twin.models import SimulationScenario, TwinSnapshot
from aetheros.twin.snapshot import clone_snapshot

BUILTIN_SCENARIOS: frozenset[str] = frozenset(
    {
        "CPU_OVERLOAD",
        "MEMORY_PRESSURE",
        "BATTERY_LOW",
        "DISK_SATURATION",
        "NODE_OFFLINE",
        "CUSTOM",
    }
)


def builtin_scenario(
    name: str,
    *,
    now: datetime | None = None,
    custom_mods: tuple[tuple[str, str], ...] = (),
) -> SimulationScenario:
    """Build one immutable built-in (or CUSTOM) scenario descriptor."""

    stamp = now if now is not None else datetime.now(UTC)
    key = name.strip().upper()
    if key not in BUILTIN_SCENARIOS:
        raise ValueError(f"Unknown scenario '{name}'")
    catalog: dict[str, tuple[str, tuple[tuple[str, str], ...]]] = {
        "CPU_OVERLOAD": (
            "Simulate elevated CPU allocation across cores.",
            (("cpu_delta", "35"), ("target", "cpu")),
        ),
        "MEMORY_PRESSURE": (
            "Simulate constrained memory headroom.",
            (("memory_delta", "25"), ("target", "memory")),
        ),
        "BATTERY_LOW": (
            "Simulate battery declining to a critical reserve.",
            (("battery_set", "10"), ("target", "battery")),
        ),
        "DISK_SATURATION": (
            "Simulate disk fill approaching capacity.",
            (("disk_delta", "40"), ("target", "disk")),
        ),
        "NODE_OFFLINE": (
            "Simulate a cluster / process node leaving the graph.",
            (("remove", "process:first"),),
        ),
        "CUSTOM": (
            "Caller-supplied twin modifications.",
            custom_mods,
        ),
    }
    description, mods = catalog[key]
    if key == "CUSTOM" and not custom_mods:
        raise ValueError("CUSTOM scenarios require modifications")
    from typing import cast

    from aetheros.twin.models import ScenarioKind

    return SimulationScenario(
        name=cast(ScenarioKind, key),
        description=description,
        modifications=mods,
        created_at=stamp,
    )


def apply_scenario(
    snapshot: TwinSnapshot,
    scenario: SimulationScenario,
    *,
    now: datetime | None = None,
) -> TwinSnapshot:
    """Apply scenario modifications to a clone — never the original snapshot."""

    cloned = clone_snapshot(snapshot, now=now)
    mods = dict(scenario.modifications)
    graph = cloned.resource_graph
    telemetry = cloned.telemetry

    if scenario.name == "CPU_OVERLOAD":
        delta = float(mods.get("cpu_delta", "35"))
        graph = _bump_resource_percent(graph, "CPU", delta)
        telemetry = _bump_telemetry(telemetry, cpu=delta)
    elif scenario.name == "MEMORY_PRESSURE":
        delta = float(mods.get("memory_delta", "25"))
        graph = _bump_resource_percent(graph, "Memory", delta)
        telemetry = _bump_telemetry(telemetry, memory=delta)
    elif scenario.name == "BATTERY_LOW":
        target = float(mods.get("battery_set", "10"))
        graph = _set_battery_percent(graph, target)
        telemetry = _bump_telemetry(telemetry, battery_set=target)
    elif scenario.name == "DISK_SATURATION":
        delta = float(mods.get("disk_delta", "40"))
        graph = _bump_resource_percent(graph, "Disk", delta)
        telemetry = _bump_telemetry(telemetry, disk=delta)
    elif scenario.name == "NODE_OFFLINE":
        graph = _remove_first_process(graph)
        telemetry = TelemetrySnapshot(
            timestamp=telemetry.timestamp,
            cpu_percent=telemetry.cpu_percent,
            memory_percent=telemetry.memory_percent,
            disk_percent=telemetry.disk_percent,
            battery_percent=telemetry.battery_percent,
            process_count=max(0, telemetry.process_count - 1),
            top_processes=telemetry.top_processes[1:]
            if telemetry.top_processes
            else (),
        )
    elif scenario.name == "CUSTOM":
        graph, telemetry = _apply_custom(graph, telemetry, mods)

    return TwinSnapshot(
        id=cloned.id,
        timestamp=cloned.timestamp,
        resource_graph=graph,
        telemetry=telemetry,
        intent=cloned.intent,
    )


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def _meta_set(node: ResourceNode, key: str, value: str) -> ResourceNode:
    """Return a node copy with one metadata key replaced/added."""

    pairs = [(k, v) for k, v in node.metadata if k != key]
    pairs.append((key, value))
    return ResourceNode(
        id=node.id,
        type=node.type,
        name=node.name,
        metadata=tuple(pairs),
        created_at=node.created_at,
    )


def _bump_resource_percent(
    graph: ResourceGraph,
    node_type: str,
    delta: float,
) -> ResourceGraph:
    """Increase percent metadata on all nodes of a type."""

    nodes: list[ResourceNode] = []
    for node in graph.nodes:
        if node.type != node_type:
            nodes.append(node)
            continue
        current = 0.0
        for key, raw in node.metadata:
            if key == "percent":
                try:
                    current = float(raw)
                except ValueError:
                    current = 0.0
                break
        nodes.append(_meta_set(node, "percent", f"{_clamp(current + delta):.1f}"))
    return ResourceGraph(
        nodes=tuple(nodes),
        edges=graph.edges,
        schema_version=graph.schema_version,
    )


def _set_battery_percent(graph: ResourceGraph, percent: float) -> ResourceGraph:
    """Set battery node percent, or leave graph unchanged when absent."""

    nodes: list[ResourceNode] = []
    found = False
    for node in graph.nodes:
        if node.type == "Battery" or node.id == "battery":
            found = True
            nodes.append(_meta_set(node, "percent", f"{_clamp(percent):.1f}"))
        else:
            nodes.append(node)
    if not found:
        return graph
    return ResourceGraph(
        nodes=tuple(nodes),
        edges=graph.edges,
        schema_version=graph.schema_version,
    )


def _remove_first_process(graph: ResourceGraph) -> ResourceGraph:
    """Drop the first Process node and its incident edges."""

    processes = nodes_of_type(graph, "Process")
    if not processes:
        return graph
    remove_id = processes[0].id
    nodes = tuple(node for node in graph.nodes if node.id != remove_id)
    edges = tuple(
        edge
        for edge in graph.edges
        if edge.source != remove_id and edge.target != remove_id
    )
    return ResourceGraph(
        nodes=nodes,
        edges=edges,
        schema_version=graph.schema_version,
    )


def _bump_telemetry(
    telemetry: TelemetrySnapshot,
    *,
    cpu: float = 0.0,
    memory: float = 0.0,
    disk: float = 0.0,
    battery_set: float | None = None,
) -> TelemetrySnapshot:
    """Return telemetry with clamped resource deltas applied."""

    battery = telemetry.battery_percent
    if battery_set is not None:
        battery = _clamp(battery_set)
    return TelemetrySnapshot(
        timestamp=telemetry.timestamp,
        cpu_percent=_clamp(telemetry.cpu_percent + cpu),
        memory_percent=_clamp(telemetry.memory_percent + memory),
        disk_percent=_clamp(telemetry.disk_percent + disk),
        battery_percent=battery,
        process_count=telemetry.process_count,
        top_processes=telemetry.top_processes,
    )


def _apply_custom(
    graph: ResourceGraph,
    telemetry: TelemetrySnapshot,
    mods: dict[str, str],
) -> tuple[ResourceGraph, TelemetrySnapshot]:
    """Apply CUSTOM modification keys to graph + telemetry."""

    cpu = float(mods.get("cpu_delta", "0") or 0)
    memory = float(mods.get("memory_delta", "0") or 0)
    disk = float(mods.get("disk_delta", "0") or 0)
    if cpu:
        graph = _bump_resource_percent(graph, "CPU", cpu)
    if memory:
        graph = _bump_resource_percent(graph, "Memory", memory)
    if disk:
        graph = _bump_resource_percent(graph, "Disk", disk)
    battery_set = mods.get("battery_set")
    tel = _bump_telemetry(
        telemetry,
        cpu=cpu,
        memory=memory,
        disk=disk,
        battery_set=float(battery_set) if battery_set is not None else None,
    )
    if mods.get("remove") == "process:first":
        graph = _remove_first_process(graph)
    return graph, tel
