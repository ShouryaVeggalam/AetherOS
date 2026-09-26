"""Diff engine — immutable before/after twin comparison."""

from __future__ import annotations

from aetheros.infra_twin.evaluator import availability_pct, mean_latency
from aetheros.infra_twin.models import InfrastructureDiff, InfrastructureSnapshot


def diff_snapshots(
    before: InfrastructureSnapshot,
    after: InfrastructureSnapshot,
) -> InfrastructureDiff:
    """Compare two twin snapshots; never mutates either side."""

    before_ids = {n.id for n in before.topology}
    after_ids = {n.id for n in after.topology}
    before_map = {n.id: n for n in before.topology}
    after_map = {n.id: n for n in after.topology}

    added = tuple(sorted(after_ids - before_ids))
    removed = tuple(sorted(before_ids - after_ids))
    changed: list[str] = []
    degraded: list[str] = []
    for node_id in sorted(before_ids & after_ids):
        left = before_map[node_id]
        right = after_map[node_id]
        if (
            left.load != right.load
            or left.latency_ms != right.latency_ms
            or left.capacity != right.capacity
            or left.available != right.available
        ):
            changed.append(node_id)
        if left.available and not right.available:
            degraded.append(node_id)
        elif right.load > left.load + 5.0 or right.latency_ms > left.latency_ms + 3.0:
            if node_id not in degraded:
                degraded.append(node_id)

    return InfrastructureDiff(
        added=added,
        removed=removed,
        changed=tuple(changed),
        degraded=tuple(sorted(degraded)),
        nodes_before=before.available_nodes,
        nodes_after=after.available_nodes,
        latency_before=round(mean_latency(before), 2),
        latency_after=round(mean_latency(after), 2),
        availability_before=round(availability_pct(before), 2),
        availability_after=round(availability_pct(after), 2),
    )
