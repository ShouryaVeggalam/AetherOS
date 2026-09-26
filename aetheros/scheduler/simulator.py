"""Scheduler simulator — evaluate plans on cloned Digital Twin snapshots.

Never modifies live topology, Resource Graph, or host telemetry.
No SSH, Kubernetes, or Docker control planes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from aetheros.scheduler.models import NodeCapacity, SchedulePlan, Workload
from aetheros.twin.evaluator import evaluate
from aetheros.twin.models import SimulationResult, TwinSnapshot
from aetheros.twin.scenario import apply_scenario, builtin_scenario
from aetheros.twin.snapshot import clone_snapshot


def simulate_plan(
    plan: SchedulePlan,
    node: NodeCapacity,
    baseline: TwinSnapshot,
    *,
    now: datetime | None = None,
) -> tuple[SchedulePlan, SimulationResult]:
    """Clone the twin, apply a CUSTOM placement load, evaluate predictions."""

    stamp = now or datetime.now(UTC)
    cloned = clone_snapshot(baseline, now=stamp)
    cpu_delta = min(40.0, plan.workload.cpu_request * 0.5)
    mem_delta = min(35.0, plan.workload.memory_request * 0.5)
    scenario = builtin_scenario(
        "CUSTOM",
        now=stamp,
        custom_mods=(
            ("cpu_delta", f"{cpu_delta:.2f}"),
            ("memory_delta", f"{mem_delta:.2f}"),
            ("target", "cpu"),
            ("label", f"schedule:{plan.workload.id}->{node.node_id}"),
        ),
    )
    simulated = apply_scenario(cloned, scenario)
    result = evaluate(baseline, simulated, scenario)
    # Latency prediction blends node latency with twin stability pressure.
    predicted_latency = round(
        node.latency_ms * (1.0 + max(0.0, result.predicted_cpu - 50.0) / 200.0),
        2,
    )
    enriched = SchedulePlan(
        workload=plan.workload,
        target_node=plan.target_node,
        score=plan.score,
        reasoning=plan.reasoning,
        predicted_cpu=result.predicted_cpu,
        predicted_memory=result.predicted_memory,
        predicted_latency_ms=predicted_latency,
    )
    return enriched, result


def simulate_plans(
    plans: Sequence[SchedulePlan],
    capacities: Mapping[str, NodeCapacity],
    baseline: TwinSnapshot,
    *,
    now: datetime | None = None,
) -> tuple[tuple[SchedulePlan, ...], tuple[SimulationResult, ...]]:
    """Simulate each candidate plan independently on cloned snapshots."""

    enriched: list[SchedulePlan] = []
    results: list[SimulationResult] = []
    for plan in plans:
        node = capacities.get(plan.target_node)
        if node is None:
            continue
        eplan, result = simulate_plan(plan, node, baseline, now=now)
        enriched.append(eplan)
        results.append(result)
    return tuple(enriched), tuple(results)


def synthetic_baseline_from_capacity(
    node: NodeCapacity,
    *,
    now: datetime | None = None,
) -> TwinSnapshot:
    """Build a minimal twin baseline from one node capacity (tests / demos)."""

    from aetheros.graph.models import ResourceEdge, ResourceGraph, ResourceNode
    from aetheros.policy_engine.models import TelemetrySnapshot
    from aetheros.twin.snapshot import create_snapshot

    stamp = now or datetime.now(UTC)
    cpu_used = 100.0 - node.available_cpu
    mem_used = 100.0 - node.available_memory
    rg = ResourceGraph(
        nodes=(
            ResourceNode(
                "cpu", "CPU", "CPU", (("percent", f"{cpu_used:.1f}"),), stamp
            ),
            ResourceNode(
                "memory",
                "Memory",
                "Memory",
                (("percent", f"{mem_used:.1f}"),),
                stamp,
            ),
            ResourceNode(
                "disk", "Disk", "Disk", (("percent", "30.0"),), stamp
            ),
            ResourceNode(
                "gpu",
                "GPU",
                "GPU",
                (("percent", f"{max(0.0, 100.0 - node.available_gpu):.1f}"),),
                stamp,
            ),
            ResourceNode(
                "net",
                "Network",
                "Network",
                (("latency_ms", f"{node.latency_ms:.1f}"),),
                stamp,
            ),
            ResourceNode(
                "proc-sched",
                "scheduler-sim",
                "Process",
                (("cpu", f"{cpu_used:.1f}"),),
                stamp,
            ),
            ResourceNode(
                "host",
                node.hostname or node.node_id,
                "Host",
                (("health", f"{node.cluster_health:.1f}"),),
                stamp,
            ),
            ResourceNode(
                "intent",
                "Scheduling",
                "Intent",
                (("name", "Scheduling"),),
                stamp,
            ),
        ),
        edges=(
            ResourceEdge("cpu", "memory", "DEPENDS_ON", 0.4),
            ResourceEdge("proc-sched", "cpu", "USES", 0.6),
            ResourceEdge("proc-sched", "memory", "USES", 0.5),
            ResourceEdge("proc-sched", "gpu", "USES", 0.3),
            ResourceEdge("host", "cpu", "CONTAINS", 0.8),
            ResourceEdge("host", "memory", "CONTAINS", 0.8),
            ResourceEdge("host", "disk", "CONTAINS", 0.5),
            ResourceEdge("host", "gpu", "CONTAINS", 0.4),
        ),
    )
    tel = TelemetrySnapshot(
        timestamp=stamp,
        cpu_percent=cpu_used,
        memory_percent=mem_used,
        disk_percent=30.0,
        battery_percent=None,
        process_count=2,
        top_processes=("scheduler-sim", node.node_id),
    )
    return create_snapshot(rg, tel, intent="Scheduling", now=stamp)
