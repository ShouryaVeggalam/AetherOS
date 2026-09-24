"""Constraint checks for orchestrator candidate nodes.

Rejects unsafe/unsuitable nodes and returns explicit reasons.
Never modifies remote systems.
"""

from __future__ import annotations

from aetheros.orchestrator.models import CandidateNode, ConstraintFailure

CPU_HARD_LIMIT = 90.0
MEMORY_HARD_LIMIT = 90.0
BATTERY_LAPTOP_FLOOR = 15.0


def evaluate_constraints(
    nodes: tuple[CandidateNode, ...] | list[CandidateNode],
) -> tuple[tuple[CandidateNode, ...], tuple[ConstraintFailure, ...]]:
    """Split candidates into eligible nodes and constraint failures.

    Args:
        nodes: Orchestrator candidate nodes.

    Returns:
        (eligible_nodes, rejected_failures).
    """

    eligible: list[CandidateNode] = []
    rejected: list[ConstraintFailure] = []
    for node in nodes:
        reason = constraint_reason(node)
        if reason is None:
            eligible.append(node)
        else:
            rejected.append(
                ConstraintFailure(
                    node_id=node.node_id,
                    hostname=node.hostname,
                    reason=reason,
                )
            )
    return tuple(eligible), tuple(rejected)


def constraint_reason(node: CandidateNode) -> str | None:
    """Return the first failing constraint reason, or None if eligible."""

    if node.health == "offline":
        return "Offline"
    if node.health == "critical":
        return "Critical health"
    if node.cpu > CPU_HARD_LIMIT:
        return f"CPU above {CPU_HARD_LIMIT:.0f}% ({node.cpu:.0f}%)"
    if node.memory > MEMORY_HARD_LIMIT:
        return f"Memory above {MEMORY_HARD_LIMIT:.0f}% ({node.memory:.0f}%)"
    if _is_laptop(node) and node.battery is not None:
        if node.battery < BATTERY_LAPTOP_FLOOR:
            return f"Battery below {BATTERY_LAPTOP_FLOOR:.0f}% ({node.battery:.0f}%)"
    return None


def _is_laptop(node: CandidateNode) -> bool:
    """Heuristic laptop detection from hostname / platform / battery."""

    name = node.hostname.lower()
    if "laptop" in name or "macbook" in name or "notebook" in name:
        return True
    if node.battery is not None and "desktop" not in name and "cloud" not in name:
        # Battery-present devices are treated as laptops for the floor rule.
        return True
    return False
