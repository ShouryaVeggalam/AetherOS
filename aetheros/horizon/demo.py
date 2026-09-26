"""Horizon Observatory demo snapshot — seeds presentation from existing APIs.

Read-only / simulation-only. Never mutates live topology, twin, or cloud state.
Consumes Cloud Federation · Infra Twin · Global Graph · Planetary Scheduler.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from aetheros.horizon.snapshot import HealthSignal, HorizonSnapshot


def build_demo_snapshot(*, now: datetime | None = None) -> HorizonSnapshot:
    """Assemble a rich demo ``HorizonSnapshot`` using existing packages only."""

    stamp = now or datetime.now(UTC)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)

    cloud_snapshot = None
    cloud_health = None
    cloud_records: tuple = ()
    cloud_age = 0.0
    connected_providers = 0
    try:
        from aetheros.cloud import seed_demo_cloud

        engine = seed_demo_cloud()
        view = engine.view(now=stamp)
        cloud_snapshot = view.snapshot
        cloud_health = view.health
        cloud_records = view.records
        connected_providers = len(cloud_records)
        cloud_age = float(view.snapshot_age_seconds)
    except Exception:
        connected_providers = 0

    topology_graph = None
    regions = 0
    clusters = 0
    nodes = 0
    try:
        from aetheros.federation import seed_demo_federation
        from aetheros.federation.registry import FederationRegistry
        from aetheros.topology import build_topology, demo_topology_metadata

        registry = FederationRegistry(online_ttl_sec=60)
        seed_demo_federation(registry, now=stamp)
        registry.refresh_statuses(now=stamp)
        topology_graph = build_topology(
            registry, metadata=demo_topology_metadata(), now=stamp
        )
        regions = len(getattr(topology_graph, "regions", ()) or ())
        clusters = len(getattr(topology_graph, "clusters", ()) or ())
        nodes = len(getattr(topology_graph, "nodes", ()) or ())
    except Exception:
        topology_graph = None

    knowledge_graph = None
    knowledge_evidence = None
    knowledge_validation = None
    discoveries = 0
    try:
        from aetheros.global_graph import build_demo_global_graph, validate_graph

        knowledge_graph, knowledge_evidence = build_demo_global_graph()
        knowledge_validation = validate_graph(knowledge_graph)
        discoveries = len(knowledge_graph.nodes_of_type("Discovery"))
        if regions == 0:
            regions = len(knowledge_graph.nodes_of_type("Region"))
        if clusters == 0:
            clusters = len(knowledge_graph.nodes_of_type("Cluster"))
        if nodes == 0:
            nodes = len(knowledge_graph.nodes_of_type("Node"))
    except Exception:
        knowledge_graph = None

    schedule_decision = None
    schedule_workload = None
    try:
        from aetheros.planetary import run_planetary_scheduler

        schedule_decision = run_planetary_scheduler(now=stamp)
        schedule_workload = schedule_decision.workload
    except Exception:
        schedule_decision = None

    twin_run = None
    twin_snapshot = None
    twin_scenarios: tuple = ()
    twin_name = ""
    active_simulations = 0
    try:
        from aetheros.infra_twin import InfrastructureTwinSimulator

        sim = InfrastructureTwinSimulator()
        twin_snapshot = sim.baseline
        twin_scenarios = sim.scenarios()
        twin_run = sim.simulate_kind("REGION_OUTAGE")
        twin_name = twin_run.scenario.name if twin_run is not None else ""
        active_simulations = 1 if twin_run is not None else 0
    except Exception:
        twin_run = None

    consensus_decision = SimpleNamespace(
        recommendation="Maintain regional failover readiness",
        confidence=88.0,
        quorum_met=True,
        votes_for=4,
        votes_against=1,
        summary="Majority favors simulated regional resilience posture.",
    )
    consensus_findings = (
        SimpleNamespace(node_id="node-a", finding="latency stable", vote="approve"),
        SimpleNamespace(node_id="node-b", finding="gpu headroom ok", vote="approve"),
        SimpleNamespace(node_id="node-c", finding="edge jitter", vote="abstain"),
    )
    consensus_conflicts = (
        SimpleNamespace(
            topic="region-failback",
            detail="node-c prefers slower failback window",
        ),
    )

    research_report = SimpleNamespace(
        title="Daily Horizon Intelligence",
        summary="Twin simulations highlight eu-central-1 as preferred inference region.",
        weekly_trends=("latency↓", "gpu demand↑", "energy efficiency↑"),
    )
    research_journal = (
        SimpleNamespace(stamp="09:00", entry="Verified graph edge Region→Cluster"),
        SimpleNamespace(stamp="11:30", entry="Twin REGION_OUTAGE simulation recorded"),
        SimpleNamespace(
            stamp="14:00", entry="Planetary scheduler demo decision cached"
        ),
    )
    research_discoveries = (
        SimpleNamespace(name="Cross-region latency corridor", confidence=91.0),
        SimpleNamespace(name="GPU expansion ROI", confidence=84.0),
    )

    consensus_confidence = float(consensus_decision.confidence)
    global_health = 92.0
    if cloud_health is not None:
        try:
            conf = float(getattr(cloud_health, "confidence", 90.0))
            if conf <= 1.0:
                conf *= 100.0
            global_health = round(0.5 * global_health + 0.5 * conf, 1)
        except Exception:
            pass

    timeline = (
        (stamp.strftime("%H:%M"), "Cloud federation snapshot seeded"),
        (stamp.strftime("%H:%M"), "Infra Twin REGION_OUTAGE evaluated"),
        (stamp.strftime("%H:%M"), "Planetary scheduler recommendation ready"),
    )

    return HorizonSnapshot(
        generated_at=stamp,
        cloud_snapshot=cloud_snapshot,
        cloud_health=cloud_health,
        cloud_records=cloud_records,
        cloud_age_seconds=cloud_age,
        topology_graph=topology_graph,
        knowledge_graph=knowledge_graph,
        knowledge_evidence=knowledge_evidence,
        knowledge_validation=knowledge_validation,
        schedule_decision=schedule_decision,
        schedule_workload=schedule_workload,
        twin_run=twin_run,
        twin_snapshot=twin_snapshot,
        twin_scenarios=twin_scenarios,
        twin_scenario_name=twin_name,
        consensus_decision=consensus_decision,
        consensus_findings=consensus_findings,
        consensus_conflicts=consensus_conflicts,
        research_report=research_report,
        research_journal=research_journal,
        research_discoveries=research_discoveries,
        global_health=global_health,
        connected_providers=connected_providers or 6,
        regions=regions or 3,
        clusters=clusters or 4,
        nodes=nodes or 8,
        discoveries=discoveries or len(research_discoveries),
        active_simulations=active_simulations,
        consensus_confidence=consensus_confidence,
        health_signals=(
            HealthSignal(
                "Federation", "green", f"{connected_providers or 6} providers"
            ),
            HealthSignal(
                "Graph",
                "green" if topology_graph is not None else "yellow",
                "topology loaded" if topology_graph is not None else "idle",
            ),
            HealthSignal(
                "Scheduler",
                "green" if schedule_decision is not None else "yellow",
                "plan ready" if schedule_decision is not None else "idle",
            ),
            HealthSignal(
                "Twin",
                "green" if twin_run is not None else "yellow",
                twin_name or "idle",
            ),
            HealthSignal(
                "Knowledge",
                "green" if knowledge_graph is not None else "yellow",
                f"{discoveries} discoveries",
            ),
            HealthSignal("Research", "green", "daily report"),
            HealthSignal("Consensus", "green", f"{consensus_confidence:.0f}%"),
        ),
        timeline_events=timeline,
    )
