"""Research analyzer — mint observations only from verified evidence.

Consumes Resource Graph, optional GraphContext, reasoning outputs,
digital-twin summaries, and historical telemetry. Never invents facts.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from aetheros.graph.models import ResourceGraph, ResourceNode
from aetheros.observatory.models import TelemetryPoint
from aetheros.research.models import ResearchObservation

_MIN_PROCESS_CPU = 8.0
_MIN_HISTORY = 3


def analyze_observations(
    *,
    graph: ResourceGraph | None = None,
    history: Sequence[TelemetryPoint] = (),
    context_label: str | None = None,
    reasoning_verified: Sequence[str] = (),
    twin_summaries: Sequence[str] = (),
    now: datetime | None = None,
) -> tuple[ResearchObservation, ...]:
    """Generate evidence-backed observations from available intelligence."""

    stamp = now or datetime.now(UTC)
    found: list[ResearchObservation] = []

    if graph is not None:
        found.extend(_from_graph(graph, stamp, context_label=context_label))
    found.extend(_from_history(history, stamp, context_label=context_label))
    for statement in reasoning_verified:
        text = statement.strip()
        if not text:
            continue
        found.append(
            _obs(
                stamp=stamp,
                title=text if text.endswith(".") else f"{text}.",
                metric="reasoning",
                value=1.0,
                evidence=(f"verified_reasoning:{text}",),
            )
        )
    for summary in twin_summaries:
        text = summary.strip()
        if not text:
            continue
        found.append(
            _obs(
                stamp=stamp,
                title=f"Simulation evidence: {text}",
                metric="simulation",
                value=1.0,
                evidence=(f"twin:{text}",),
            )
        )
    return tuple(found)


def meta_float(node: ResourceNode, *keys: str, default: float = 0.0) -> float:
    """Read the first present metadata key as float."""

    data = dict(node.metadata)
    for key in keys:
        raw = data.get(key)
        if raw is None:
            continue
        try:
            return float(raw)
        except ValueError:
            continue
    return default


def _from_graph(
    graph: ResourceGraph,
    stamp: datetime,
    *,
    context_label: str | None,
) -> list[ResearchObservation]:
    out: list[ResearchObservation] = []
    processes = [n for n in graph.nodes if n.type == "Process"]
    cpu_nodes = [n for n in graph.nodes if n.type == "CPU"]
    if processes and cpu_nodes:
        top = max(processes, key=lambda n: meta_float(n, "cpu_percent"))
        cpu_pct = meta_float(top, "cpu_percent")
        if cpu_pct >= _MIN_PROCESS_CPU:
            path = f"{top.id} --USES--> {cpu_nodes[0].id}"
            for edge in graph.edges:
                if (
                    edge.source == top.id
                    and edge.target == cpu_nodes[0].id
                    and edge.relationship == "USES"
                ):
                    path = f"{edge.source} --{edge.relationship}--> {edge.target}"
                    break
            label = context_label or "workload"
            out.append(
                _obs(
                    stamp=stamp,
                    title=(
                        f"{label.title()} process {top.name} accounted for "
                        f"{cpu_pct:.0f}% CPU utilization."
                    ),
                    metric="cpu",
                    value=cpu_pct,
                    evidence=(
                        path,
                        f"process_metrics.cpu_percent={cpu_pct:.2f}",
                        f"graph_nodes={len(graph.nodes)}",
                    ),
                )
            )
    mem_nodes = [n for n in graph.nodes if n.type == "Memory"]
    if mem_nodes:
        mem = mem_nodes[0]
        used = meta_float(mem, "percent", "used_percent")
        if used >= 70.0:
            out.append(
                _obs(
                    stamp=stamp,
                    title=f"Memory utilization reached {used:.0f}%.",
                    metric="memory",
                    value=used,
                    evidence=(f"node:{mem.id}", f"memory.percent={used:.2f}"),
                )
            )
    disk_nodes = [n for n in graph.nodes if n.type == "Disk"]
    if disk_nodes:
        disk = disk_nodes[0]
        used = meta_float(disk, "percent", "used_percent")
        if used >= 80.0:
            out.append(
                _obs(
                    stamp=stamp,
                    title=f"Disk utilization reached {used:.0f}%.",
                    metric="disk",
                    value=used,
                    evidence=(f"node:{disk.id}", f"disk.percent={used:.2f}"),
                )
            )
    return out


def _from_history(
    history: Sequence[TelemetryPoint],
    stamp: datetime,
    *,
    context_label: str | None,
) -> list[ResearchObservation]:
    if len(history) < _MIN_HISTORY:
        return []
    first = history[0]
    last = history[-1]
    delta = last.cpu - first.cpu
    if abs(delta) < 5.0:
        return []
    direction = "increased" if delta > 0 else "decreased"
    label = context_label or (last.intent or "workload")
    return [
        _obs(
            stamp=stamp,
            title=(
                f"{label} workloads {direction} CPU utilization by "
                f"{abs(delta):.0f}% across {len(history)} samples."
            ),
            metric="cpu",
            value=abs(delta),
            evidence=(
                f"history_start_cpu={first.cpu:.2f}",
                f"history_end_cpu={last.cpu:.2f}",
                f"sample_count={len(history)}",
                f"window_start={first.timestamp.isoformat()}",
                f"window_end={last.timestamp.isoformat()}",
            ),
        )
    ]


def _obs(
    *,
    stamp: datetime,
    title: str,
    metric: str,
    value: float,
    evidence: tuple[str, ...],
) -> ResearchObservation:
    digest = hashlib.sha1(
        f"{title}|{metric}|{value}|{evidence}".encode(),
        usedforsecurity=False,
    ).hexdigest()[:12]
    return ResearchObservation(
        id=f"obs_{digest}",
        timestamp=stamp,
        title=title,
        metric=metric,
        value=value,
        evidence=evidence,
    )


def context_label_from_mapping(
    context: Mapping[str, Any] | object | None,
) -> str | None:
    """Extract a display label from a loose context mapping or GraphContext-like object."""

    if context is None:
        return None
    if hasattr(context, "active_intent"):
        intent = getattr(context, "active_intent", None)
        name = getattr(intent, "name", None)
        if isinstance(name, str) and name.strip():
            return name.strip()
    if isinstance(context, Mapping):
        for key in ("intent", "active_intent", "label", "context"):
            value = context.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if hasattr(value, "name"):
                name = getattr(value, "name", None)
                if isinstance(name, str) and name.strip():
                    return name.strip()
    return None
