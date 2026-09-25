"""Digital Twin diff engine — compare baseline vs simulated snapshots."""

from __future__ import annotations

from aetheros.graph.models import ResourceEdge
from aetheros.twin.models import MetricChange, SnapshotDiff, TwinSnapshot


def diff_twins(before: TwinSnapshot, after: TwinSnapshot) -> SnapshotDiff:
    """Compute immutable topology + metric differences."""

    before_ids = before.resource_graph.node_ids()
    after_ids = after.resource_graph.node_ids()
    before_edges = frozenset(_edge_key(edge) for edge in before.resource_graph.edges)
    after_edges = frozenset(_edge_key(edge) for edge in after.resource_graph.edges)
    metrics = (
        MetricChange(
            "cpu",
            before.telemetry.cpu_percent,
            after.telemetry.cpu_percent,
        ),
        MetricChange(
            "memory",
            before.telemetry.memory_percent,
            after.telemetry.memory_percent,
        ),
        MetricChange(
            "disk",
            before.telemetry.disk_percent,
            after.telemetry.disk_percent,
        ),
        MetricChange(
            "battery",
            before.telemetry.battery_percent,
            after.telemetry.battery_percent,
        ),
    )
    changed = tuple(item for item in metrics if item.before != item.after)
    return SnapshotDiff(
        added_nodes=after_ids - before_ids,
        removed_nodes=before_ids - after_ids,
        changed_metrics=changed,
        changed_edges=(after_edges - before_edges) | (before_edges - after_edges),
    )


def format_metric_lines(diff: SnapshotDiff) -> tuple[str, ...]:
    """Human-readable metric delta lines for panels/tests."""

    lines: list[str] = []
    for change in diff.changed_metrics:
        before = _fmt(change.before)
        after = _fmt(change.after)
        lines.append(f"{change.metric.upper()}  {before} → {after}")
    return tuple(lines)


def _edge_key(edge: ResourceEdge) -> str:
    return f"{edge.source}->{edge.target}:{edge.relationship}"


def _fmt(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.0f}%"
