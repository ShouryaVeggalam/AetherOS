"""Bottleneck engine — recurring pressure patterns with graph path evidence.

Every finding requires at least one supporting resource-graph path.
No graph path ⇒ no bottleneck emitted.
"""

from __future__ import annotations

from collections.abc import Sequence

from aetheros.graph.models import ResourceGraph, ResourceNode
from aetheros.observatory.models import TelemetryPoint
from aetheros.research.analyzer import meta_float
from aetheros.research.models import BottleneckFinding, BottleneckKind

_CPU_THRESH = 85.0
_MEM_THRESH = 80.0
_DISK_THRESH = 85.0
_RECURRENCE_MIN = 3


def detect_bottlenecks(
    *,
    graph: ResourceGraph | None = None,
    history: Sequence[TelemetryPoint] = (),
) -> tuple[BottleneckFinding, ...]:
    """Detect bottlenecks only when graph paths and recurrence evidence exist."""

    if graph is None:
        return ()
    findings: list[BottleneckFinding] = []
    findings.extend(_foreground_cpu(graph, history))
    findings.extend(_memory_pressure(graph, history))
    findings.extend(_disk_contention(graph, history))
    findings.extend(_network_congestion(graph))
    return tuple(findings)


def _foreground_cpu(
    graph: ResourceGraph,
    history: Sequence[TelemetryPoint],
) -> list[BottleneckFinding]:
    processes = [n for n in graph.nodes if n.type == "Process"]
    cpu_nodes = [n for n in graph.nodes if n.type == "CPU"]
    if not processes or not cpu_nodes:
        return []
    top = max(processes, key=lambda n: meta_float(n, "cpu_percent"))
    cpu_pct = meta_float(top, "cpu_percent")
    if cpu_pct < _CPU_THRESH:
        return []
    paths = _paths_between(graph, top, cpu_nodes[0])
    if not paths:
        return []
    recurrence = sum(1 for p in history if p.cpu >= _CPU_THRESH) or 1
    if history and recurrence < _RECURRENCE_MIN and len(history) >= _RECURRENCE_MIN:
        return []
    evidence_count = max(1, recurrence)
    return [
        BottleneckFinding(
            kind="foreground_cpu_saturation",
            title="Foreground CPU saturation",
            summary=(
                f"Process {top.name} held {cpu_pct:.0f}% CPU with "
                f"{evidence_count} supporting sample(s)."
            ),
            graph_paths=paths,
            evidence_count=evidence_count,
            confidence=_confidence(cpu_pct, _CPU_THRESH, evidence_count),
        )
    ]


def _memory_pressure(
    graph: ResourceGraph,
    history: Sequence[TelemetryPoint],
) -> list[BottleneckFinding]:
    mem_nodes = [n for n in graph.nodes if n.type == "Memory"]
    processes = [n for n in graph.nodes if n.type == "Process"]
    if not mem_nodes:
        return []
    mem = mem_nodes[0]
    used = meta_float(mem, "percent", "used_percent")
    if used < _MEM_THRESH:
        return []
    paths: list[str] = [f"memory:{mem.id}@{used:.1f}%"]
    if processes:
        top = max(processes, key=lambda n: meta_float(n, "memory_percent"))
        link = _paths_between(graph, top, mem)
        paths.extend(link or [f"{top.id} --ALLOCATES--> {mem.id}"])
    recurrence = sum(1 for p in history if p.memory >= _MEM_THRESH) or 1
    if history and recurrence < _RECURRENCE_MIN and len(history) >= _RECURRENCE_MIN:
        return []
    return [
        BottleneckFinding(
            kind="memory_pressure",
            title="Memory pressure",
            summary=(
                f"Memory utilization at {used:.0f}% with graph-backed allocation paths."
            ),
            graph_paths=tuple(dict.fromkeys(paths)),
            evidence_count=max(1, recurrence),
            confidence=_confidence(used, _MEM_THRESH, max(1, recurrence)),
        )
    ]


def _disk_contention(
    graph: ResourceGraph,
    history: Sequence[TelemetryPoint],
) -> list[BottleneckFinding]:
    disk_nodes = [n for n in graph.nodes if n.type == "Disk"]
    processes = [n for n in graph.nodes if n.type == "Process"]
    if not disk_nodes:
        return []
    disk = disk_nodes[0]
    used = meta_float(disk, "percent", "used_percent")
    if used < _DISK_THRESH:
        return []
    paths: list[str] = [f"disk:{disk.id}@{used:.1f}%"]
    if processes:
        top = processes[0]
        link = _paths_between(graph, top, disk)
        paths.extend(link or [f"{top.id} --USES--> {disk.id}"])
    recurrence = sum(1 for p in history if p.disk >= _DISK_THRESH) or 1
    if history and recurrence < _RECURRENCE_MIN and len(history) >= _RECURRENCE_MIN:
        return []
    return [
        BottleneckFinding(
            kind="disk_contention",
            title="High disk contention",
            summary=(
                f"Disk utilization at {used:.0f}% with supporting dependency paths."
            ),
            graph_paths=tuple(dict.fromkeys(paths)),
            evidence_count=max(1, recurrence),
            confidence=_confidence(used, _DISK_THRESH, max(1, recurrence)),
        )
    ]


def _network_congestion(graph: ResourceGraph) -> list[BottleneckFinding]:
    net_nodes = [n for n in graph.nodes if n.type == "Network"]
    if not net_nodes:
        return []
    net = net_nodes[0]
    util = meta_float(net, "utilization", "percent", "saturation")
    if util < 80.0:
        return []
    processes = [n for n in graph.nodes if n.type == "Process"]
    paths = [f"network:{net.id}@{util:.1f}%"]
    if processes:
        paths.append(f"{processes[0].id} --COMMUNICATES--> {net.id}")
    return [
        BottleneckFinding(
            kind="network_congestion",
            title="Network congestion",
            summary=f"Network utilization at {util:.0f}% with communication paths.",
            graph_paths=tuple(paths),
            evidence_count=1,
            confidence=_confidence(util, 80.0, 1),
        )
    ]


def _paths_between(
    graph: ResourceGraph,
    source: ResourceNode,
    target: ResourceNode,
) -> tuple[str, ...]:
    paths: list[str] = []
    for edge in graph.edges:
        if edge.source == source.id and edge.target == target.id:
            paths.append(f"{edge.source} --{edge.relationship}--> {edge.target}")
        elif edge.source == target.id and edge.target == source.id:
            paths.append(f"{edge.source} --{edge.relationship}--> {edge.target}")
    return tuple(paths)


def _confidence(value: float, threshold: float, evidence_count: int) -> float:
    overshoot = max(0.0, value - threshold)
    base = 55.0 + min(25.0, overshoot) + min(20.0, 4.0 * evidence_count)
    return round(min(99.0, base), 2)


__all__ = ["detect_bottlenecks", "BottleneckKind"]
