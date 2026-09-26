"""Atlas demo snapshot builder — seeds presentation data from existing APIs.

Read-only / simulation-only. Never mutates live topology or telemetry stores.
"""

from __future__ import annotations

from datetime import UTC, datetime

from aetheros.atlas.snapshot import AtlasSnapshot, HealthSignal
from aetheros.federation import PROTOCOL_VERSION, seed_demo_federation
from aetheros.federation.registry import FederationRegistry
from aetheros.scheduler import (
    ScheduleConstraint,
    demo_nodes,
    demo_workload,
    run_scheduler,
)
from aetheros.topology import build_topology, demo_topology_metadata
from aetheros.twin import builtin_scenario, evaluate
from aetheros.twin.scenario import apply_scenario
from aetheros.twin.snapshot import clone_snapshot


def build_demo_snapshot(*, now: datetime | None = None) -> AtlasSnapshot:
    """Assemble a rich demo ``AtlasSnapshot`` using existing packages only."""

    stamp = now or datetime.now(UTC)
    registry = FederationRegistry(online_ttl_sec=60)
    beats, _sync = seed_demo_federation(registry, now=stamp)
    registry.refresh_statuses(now=stamp)
    view = registry.view()
    graph = build_topology(registry, metadata=demo_topology_metadata(), now=stamp)

    workload = demo_workload()
    schedule = run_scheduler(
        workload,
        demo_nodes(),
        constraints=(
            ScheduleConstraint(kind="REQUIRE_GPU", value=1.0),
            ScheduleConstraint(kind="AVOID_OVERLOAD", value=85.0),
        ),
        now=stamp,
    )

    # Twin: clone synthetic baseline from scheduler path when available.
    twin_report = None
    twin_baseline = None
    twin_name = ""
    try:
        from aetheros.scheduler.simulator import synthetic_baseline_from_capacity

        seed_node = demo_nodes()[1]
        twin_baseline = synthetic_baseline_from_capacity(seed_node, now=stamp)
        scenario = builtin_scenario("CPU_OVERLOAD", now=stamp)
        simulated = apply_scenario(clone_snapshot(twin_baseline, now=stamp), scenario)
        result = evaluate(twin_baseline, simulated, scenario)
        from aetheros.twin.diff import diff_twins
        from aetheros.twin.simulator import DigitalTwinReport

        twin_report = DigitalTwinReport(
            baseline=twin_baseline,
            simulated=simulated,
            result=result,
            diff=diff_twins(twin_baseline, simulated),
        )
        twin_name = scenario.name
    except Exception:
        twin_report = None

    online = sum(1 for n in view.nodes if str(getattr(n, "status", "")) == "online")
    connected = len(view.nodes)
    cluster_health = 0.0
    try:
        from aetheros.topology import all_cluster_health

        healths = all_cluster_health(graph)
        if healths:
            scores = []
            for h in healths:
                status = str(getattr(h, "status", "empty"))
                if status == "healthy":
                    scores.append(90.0)
                elif status == "degraded":
                    scores.append(60.0)
                elif status == "critical":
                    scores.append(25.0)
                else:
                    scores.append(40.0)
            cluster_health = sum(scores) / len(scores)
    except Exception:
        cluster_health = float(getattr(schedule, "cluster_health", 70.0))

    return AtlasSnapshot(
        generated_at=stamp,
        federation_registry=view,
        federation_heartbeats=tuple(beats),
        protocol_version=PROTOCOL_VERSION,
        topology_graph=graph,
        schedule_result=schedule,
        schedule_workload=workload,
        consensus_decision=None,
        consensus_findings=(),
        consensus_conflicts=(),
        twin_report=twin_report,
        twin_scenario_name=twin_name,
        twin_baseline=twin_baseline,
        research_report=None,
        research_journal=(),
        cpu_percent=42.0,
        memory_percent=55.0,
        disk_percent=31.0,
        connected_nodes=connected,
        online_nodes=online,
        cluster_health=cluster_health,
        discoveries=0,
        active_simulations=1 if twin_report is not None else 0,
        health_signals=(
            HealthSignal("Telemetry", "green", "demo host"),
            HealthSignal("Graph", "green", "topology loaded"),
            HealthSignal("Memory", "green", "55%"),
            HealthSignal("Reasoning", "yellow", "no consensus yet"),
            HealthSignal("Scheduler", "green", "plan ready"),
            HealthSignal("Consensus", "yellow", "idle"),
            HealthSignal("Federation", "green", f"{online} online"),
        ),
    )
