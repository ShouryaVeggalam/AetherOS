"""Hard scheduling constraints — reject invalid placements before scoring.

Simulation gate only. Never starts containers or touches live nodes.
"""

from __future__ import annotations

from collections.abc import Sequence

from aetheros.scheduler.models import (
    NodeCapacity,
    ScheduleConstraint,
    Workload,
)


def check_constraints(
    workload: Workload,
    node: NodeCapacity,
    constraints: Sequence[ScheduleConstraint] = (),
) -> tuple[bool, str]:
    """Return ``(accepted, reason)`` for one workload→node pair."""

    # Intrinsic capacity gate (always on).
    if workload.cpu_request > node.available_cpu + 1e-9:
        return False, "insufficient CPU capacity"
    if workload.memory_request > node.available_memory + 1e-9:
        return False, "insufficient memory capacity"
    if workload.gpu_request > node.available_gpu + 1e-9:
        return False, "insufficient GPU capacity"

    for constraint in constraints:
        ok, reason = _apply_one(workload, node, constraint)
        if not ok:
            return False, reason
    return True, "ok"


def filter_candidates(
    workload: Workload,
    nodes: Sequence[NodeCapacity],
    constraints: Sequence[ScheduleConstraint] = (),
) -> tuple[tuple[NodeCapacity, ...], tuple[tuple[str, str], ...]]:
    """Split nodes into accepted candidates and rejected ``(node_id, reason)``."""

    accepted: list[NodeCapacity] = []
    rejected: list[tuple[str, str]] = []
    for node in nodes:
        ok, reason = check_constraints(workload, node, constraints)
        if ok:
            accepted.append(node)
        else:
            rejected.append((node.node_id, reason))
    return tuple(accepted), tuple(rejected)


def _apply_one(
    workload: Workload,
    node: NodeCapacity,
    constraint: ScheduleConstraint,
) -> tuple[bool, str]:
    kind = constraint.kind
    if kind == "MAX_CPU":
        limit = float(constraint.value)
        projected = node.utilization + workload.cpu_request * 0.5
        if projected > limit + 1e-9:
            return False, f"MAX_CPU exceeded ({projected:.1f}>{limit:.1f})"
        return True, "ok"
    if kind == "MAX_MEMORY":
        limit = float(constraint.value)
        # Memory headroom after request must remain below limit utilization.
        used = 100.0 - node.available_memory
        projected = used + workload.memory_request
        if projected > limit + 1e-9:
            return False, f"MAX_MEMORY exceeded ({projected:.1f}>{limit:.1f})"
        return True, "ok"
    if kind == "REQUIRE_GPU":
        need = float(constraint.value) if constraint.value != "" else 1.0
        need = max(need, workload.gpu_request)
        if node.available_gpu + 1e-9 < need:
            return False, "REQUIRE_GPU not satisfied"
        return True, "ok"
    if kind == "REGION_LOCK":
        region = str(constraint.value).strip().lower()
        if not region:
            return False, "REGION_LOCK value empty"
        if node.region_id.strip().lower() != region:
            return False, f"REGION_LOCK requires {region}"
        return True, "ok"
    if kind == "AVOID_OVERLOAD":
        threshold = float(constraint.value) if constraint.value != "" else 85.0
        if node.utilization > threshold + 1e-9:
            return False, f"AVOID_OVERLOAD utilization {node.utilization:.1f}"
        return True, "ok"
    return False, f"unknown constraint {kind}"
