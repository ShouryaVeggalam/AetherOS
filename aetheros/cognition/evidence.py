"""Evidence collector — mint Evidence only from real graph / telemetry / twin inputs.

Deterministic. No LLM. Empty inputs ⇒ empty evidence.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from aetheros.cognition.models import Evidence
from aetheros.graph.models import ResourceGraph, ResourceNode
from aetheros.observatory.models import TelemetryPoint


def collect_evidence(
    *,
    graph: ResourceGraph | None = None,
    history: Sequence[TelemetryPoint] = (),
    context: Mapping[str, Any] | object | str | None = None,
    twin_summaries: Sequence[str] = (),
    memory_patterns: Sequence[str] = (),
    now: datetime | None = None,
) -> tuple[Evidence, ...]:
    """Gather immutable evidence artifacts from available intelligence inputs."""

    stamp = now or datetime.now(UTC)
    items: list[Evidence] = []
    if graph is not None:
        items.extend(_from_graph(graph, stamp))
    items.extend(_from_history(history, stamp))
    items.extend(_from_context(context, stamp))
    for summary in twin_summaries:
        text = summary.strip()
        if not text:
            continue
        items.append(
            _evidence(
                source="digital_twin",
                metric="simulation",
                value=1.0,
                stamp=stamp,
                salt=text,
            )
        )
    for pattern in memory_patterns:
        text = pattern.strip()
        if not text:
            continue
        items.append(
            _evidence(
                source="operational_memory",
                metric="pattern",
                value=1.0,
                stamp=stamp,
                salt=text,
            )
        )
    return tuple(items)


def _meta_float(node: ResourceNode, *keys: str, default: float = 0.0) -> float:
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


def _from_graph(graph: ResourceGraph, stamp: datetime) -> list[Evidence]:
    out: list[Evidence] = []
    for node in graph.nodes:
        if node.type in {"CPU", "Memory", "Disk", "Battery", "Network"}:
            value = _meta_float(node, "percent", "utilization", "cpu_percent")
            out.append(
                _evidence(
                    source="resource_graph",
                    metric=f"node:{node.id}",
                    value=value,
                    stamp=stamp,
                    salt=f"{node.type}:{node.id}:{value}",
                )
            )
        if node.type == "Process":
            cpu = _meta_float(node, "cpu_percent")
            if cpu > 0:
                out.append(
                    _evidence(
                        source="resource_graph",
                        metric=f"process_cpu:{node.id}",
                        value=cpu,
                        stamp=stamp,
                        salt=f"proc:{node.id}:{cpu}",
                    )
                )
    for edge in graph.edges:
        out.append(
            _evidence(
                source="resource_graph",
                metric=f"path:{edge.source}→{edge.target}",
                value=edge.weight * 100.0,
                stamp=stamp,
                salt=f"{edge.source}:{edge.relationship}:{edge.target}",
            )
        )
    return out


def _from_history(history: Sequence[TelemetryPoint], stamp: datetime) -> list[Evidence]:
    if len(history) < 2:
        return []
    first, last = history[0], history[-1]
    return [
        _evidence(
            source="telemetry_history",
            metric="cpu_delta",
            value=last.cpu - first.cpu,
            stamp=stamp,
            salt=f"cpu:{first.cpu}:{last.cpu}:{len(history)}",
        ),
        _evidence(
            source="telemetry_history",
            metric="memory_delta",
            value=last.memory - first.memory,
            stamp=stamp,
            salt=f"mem:{first.memory}:{last.memory}:{len(history)}",
        ),
        _evidence(
            source="telemetry_history",
            metric="sample_count",
            value=float(len(history)),
            stamp=stamp,
            salt=f"n:{len(history)}",
        ),
    ]


def _from_context(
    context: Mapping[str, Any] | object | str | None,
    stamp: datetime,
) -> list[Evidence]:
    label = _context_label(context)
    if label is None:
        return []
    return [
        _evidence(
            source="graph_context",
            metric="active_intent",
            value=1.0,
            stamp=stamp,
            salt=f"intent:{label}",
        )
    ]


def context_label(context: Mapping[str, Any] | object | str | None) -> str:
    """Resolve a display context label with BALANCED fallback."""

    return _context_label(context) or "BALANCED"


def _context_label(context: Mapping[str, Any] | object | str | None) -> str | None:
    if context is None:
        return None
    if isinstance(context, str):
        text = context.strip()
        return text or None
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
            name = getattr(value, "name", None)
            if isinstance(name, str) and name.strip():
                return name.strip()
    return None


def _evidence(
    *,
    source: str,
    metric: str,
    value: float,
    stamp: datetime,
    salt: str,
) -> Evidence:
    digest = hashlib.sha1(
        f"{source}|{metric}|{value}|{salt}".encode(),
        usedforsecurity=False,
    ).hexdigest()[:12]
    return Evidence(
        id=f"ev_{digest}",
        source=source,  # type: ignore[arg-type]
        metric=metric,
        value=value,
        timestamp=stamp,
    )
