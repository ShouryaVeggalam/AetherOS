"""Explainability helpers for orchestrator execution plans.

Every line is grounded in scores, constraints, or node metrics.
"""

from __future__ import annotations

from aetheros.orchestrator.models import (
    CandidateNode,
    ConstraintFailure,
    NodeScore,
    WorkloadProfile,
)


def explain_plan(
    workload: WorkloadProfile,
    winner: NodeScore | None,
    rejected: tuple[ConstraintFailure, ...],
    ranked: tuple[NodeScore, ...],
) -> tuple[str, ...]:
    """Build evidence-based explanation lines for an ExecutionPlan."""

    lines: list[str] = [
        f"Workload: {workload.name} — {workload.description}",
    ]
    if winner is None:
        lines.append("No eligible node satisfied constraints.")
        lines.extend(_rejected_lines(rejected))
        return tuple(lines)

    node = winner.node
    lines.append(f"Recommended node: {node.hostname} (score {winner.score}).")
    lines.extend(f"• {item}" for item in winner.breakdown[:4])
    lines.extend(_why_best(node, winner, ranked))
    lines.extend(_rejected_lines(rejected))
    if len(ranked) > 1:
        runner = ranked[1]
        lines.append(f"Next best: {runner.node.hostname} scored {runner.score}.")
    return tuple(lines)


def _why_best(
    node: CandidateNode,
    winner: NodeScore,
    ranked: tuple[NodeScore, ...],
) -> list[str]:
    """Add comparative why-lines when peers exist."""

    extras: list[str] = []
    if node.battery is None:
        extras.append(f"• {node.hostname} is on AC power (no battery constraint).")
    elif node.battery >= 50:
        extras.append(f"• Battery comfortable at {node.battery:.0f}%.")
    if node.gpu >= 70:
        extras.append(f"• GPU available (score {node.gpu:.0f}).")
    if ranked:
        lowest_cpu = min(ranked, key=lambda s: s.node.cpu)
        if lowest_cpu.node.node_id == node.node_id:
            extras.append("• Lowest CPU load among eligible nodes.")
        highest_mem = max(ranked, key=lambda s: 100.0 - s.node.memory)
        if highest_mem.node.node_id == node.node_id:
            extras.append("• Highest available memory among eligible nodes.")
    return extras[:3]


def _rejected_lines(rejected: tuple[ConstraintFailure, ...]) -> list[str]:
    """Format rejected node reasons."""

    if not rejected:
        return ["Rejected: none."]
    lines = ["Rejected:"]
    for item in rejected[:6]:
        lines.append(f"• {item.hostname}: {item.reason}")
    return lines
