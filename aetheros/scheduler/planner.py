"""Scheduling planner — generate and rank candidate placements.

Produces top-N ``SchedulePlan`` recommendations. Never executes workloads.
"""

from __future__ import annotations

from collections.abc import Sequence

from aetheros.scheduler.constraints import filter_candidates
from aetheros.scheduler.models import (
    NodeCapacity,
    ScheduleConstraint,
    SchedulePlan,
    Workload,
)
from aetheros.scheduler.scoring import ScoreWeights, score_node


def plan_placements(
    workload: Workload,
    nodes: Sequence[NodeCapacity],
    *,
    constraints: Sequence[ScheduleConstraint] = (),
    weights: ScoreWeights | None = None,
    top_n: int = 3,
) -> tuple[tuple[SchedulePlan, ...], tuple[tuple[str, str], ...]]:
    """Filter by constraints, score survivors, return top ``top_n`` plans."""

    if top_n < 1:
        raise ValueError("top_n must be >= 1")
    accepted, rejected = filter_candidates(workload, nodes, constraints)
    scored: list[SchedulePlan] = []
    for node in accepted:
        score, reasoning = score_node(workload, node, weights=weights)
        scored.append(
            SchedulePlan(
                workload=workload,
                target_node=node.node_id,
                score=score,
                reasoning=reasoning,
            )
        )
    scored.sort(key=lambda p: (-p.score, p.target_node))
    return tuple(scored[:top_n]), rejected


def demo_workload() -> Workload:
    """Sample AI Training workload for dashboard / tests (simulation only)."""

    return Workload(
        id="wl-ai-train",
        name="AI Training",
        cpu_request=30.0,
        memory_request=40.0,
        gpu_request=10.0,
        priority=80.0,
    )


def demo_nodes() -> tuple[NodeCapacity, ...]:
    """Three candidate nodes with differentiated capacity / latency / health."""

    return (
        NodeCapacity(
            node_id="A",
            available_cpu=55.0,
            available_memory=50.0,
            available_gpu=15.0,
            utilization=45.0,
            latency_ms=8.0,
            region_id="us-east",
            cluster_health=75.0,
            hostname="node-a",
        ),
        NodeCapacity(
            node_id="B",
            available_cpu=85.0,
            available_memory=80.0,
            available_gpu=50.0,
            utilization=25.0,
            latency_ms=3.0,
            region_id="us-east",
            cluster_health=92.0,
            hostname="node-b",
        ),
        NodeCapacity(
            node_id="C",
            available_cpu=45.0,
            available_memory=75.0,
            available_gpu=25.0,
            utilization=50.0,
            latency_ms=12.0,
            region_id="eu-west",
            cluster_health=80.0,
            hostname="node-c",
        ),
    )


def capacities_from_topology_heartbeats(
    nodes: Sequence[object],
) -> tuple[NodeCapacity, ...]:
    """Derive ``NodeCapacity`` from topology ``TopologyNode``-like objects.

    Uses heartbeat fields when present. Never invents GPU when absent (0).
    """

    out: list[NodeCapacity] = []
    for node in nodes:
        node_id = str(getattr(node, "node_id", "")).strip()
        if not node_id:
            continue
        hb = getattr(node, "heartbeat", None)
        status = str(getattr(node, "status", "unknown"))
        region = str(getattr(node, "region_id", "") or "")
        hostname = str(getattr(node, "hostname", "") or node_id)
        if hb is not None:
            cpu_used = float(hb.cpu)
            mem_used = float(hb.memory)
            network = float(hb.network)
            available_cpu = max(0.0, 100.0 - cpu_used)
            available_memory = max(0.0, 100.0 - mem_used)
            utilization = max(cpu_used, mem_used)
            latency = max(1.0, network)
        else:
            available_cpu = 50.0 if status == "online" else 0.0
            available_memory = 50.0 if status == "online" else 0.0
            utilization = 50.0 if status == "online" else 100.0
            latency = 20.0
        health = 90.0 if status == "online" else 20.0 if status == "offline" else 50.0
        # GPU not in heartbeat — leave 0 unless node exposes available_gpu.
        gpu = float(getattr(node, "available_gpu", 0.0) or 0.0)
        out.append(
            NodeCapacity(
                node_id=node_id,
                available_cpu=available_cpu,
                available_memory=available_memory,
                available_gpu=gpu,
                utilization=utilization,
                latency_ms=latency,
                region_id=region,
                cluster_health=health,
                hostname=hostname,
            )
        )
    return tuple(out)
