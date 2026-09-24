"""Workload planner — recommend the best cluster node for a workload.

Recommendation-only. Never executes, SSHes, or modifies remote systems.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.cluster.models import ClusterNode, NodeHealth
from aetheros.cluster.node import classify_health
from aetheros.orchestrator.constraints import evaluate_constraints
from aetheros.orchestrator.explain import explain_plan
from aetheros.orchestrator.models import CandidateNode, ExecutionPlan, WorkloadProfile
from aetheros.orchestrator.scorer import score_nodes
from aetheros.orchestrator.workload import get_workload


@dataclass
class ResourcePlanner:
    """Plan optimal node placement for a workload across cluster nodes."""

    def plan(
        self,
        workload: WorkloadProfile | str,
        nodes: tuple[ClusterNode, ...] | list[ClusterNode],
        *,
        online_ids: frozenset[str] | set[str] | None = None,
    ) -> ExecutionPlan:
        """Build an ExecutionPlan for the given workload and cluster nodes.

        Args:
            workload: Workload profile or catalog name.
            nodes: Cluster nodes from the registry/aggregator.
            online_ids: Node ids considered online (for health).

        Returns:
            Immutable ExecutionPlan (recommendation only).
        """

        profile = (
            workload
            if isinstance(workload, WorkloadProfile)
            else get_workload(workload)
        )
        online = frozenset(online_ids) if online_ids is not None else None
        candidates = tuple(
            to_candidate(
                node,
                online=(True if online is None else node.node_id in online),
            )
            for node in nodes
        )
        eligible, rejected = evaluate_constraints(candidates)
        ranked = score_nodes(eligible, profile)
        winner = ranked[0] if ranked else None
        explanation = explain_plan(profile, winner, rejected, ranked)
        return ExecutionPlan(
            workload=profile,
            recommended_node=winner.node if winner else None,
            score=winner.score if winner else 0,
            rejected_nodes=rejected,
            ranked=ranked,
            explanation=explanation,
        )


def to_candidate(node: ClusterNode, *, online: bool) -> CandidateNode:
    """Adapt a cluster ClusterNode into an orchestrator CandidateNode."""

    health: NodeHealth = classify_health(node, online=online)
    return CandidateNode(
        node_id=node.node_id,
        hostname=node.hostname,
        cpu=node.cpu,
        memory=node.memory,
        disk=node.disk,
        battery=node.battery,
        gpu=infer_gpu(node),
        network_latency=node.latency,
        platform=node.platform,
        health=health,
    )


def infer_gpu(node: ClusterNode) -> float:
    """Infer a GPU availability score from hostname/platform heuristics.

    No remote probing — recommendation layer only.
    """

    name = node.hostname.lower()
    if "desktop" in name or "workstation" in name:
        return 90.0
    if "cloud" in name or "gpu" in name:
        return 85.0
    if "pi" in name or "raspberry" in name:
        return 5.0
    if "laptop" in name or "macbook" in name:
        return 45.0
    # Unknown hosts: modest GPU assumption.
    return 30.0
