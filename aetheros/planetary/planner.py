"""Planetary planner — end-to-end read-only placement recommendations.

Pipeline: constrain → score/evaluate → twin-simulate → optimize top-5.
Never deploys workloads, never calls Kubernetes / cloud / Terraform.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from aetheros.infra_twin.models import InfrastructureSnapshot
from aetheros.planetary.constraints import filter_candidates
from aetheros.planetary.evaluator import (
    evaluate_sites,
    refine_score_with_simulation,
)
from aetheros.planetary.models import (
    GlobalWorkload,
    PlacementSite,
    PlanetaryConstraint,
    ScheduleDecision,
)
from aetheros.planetary.optimizer import decision_from_ranked, optimize_placements
from aetheros.planetary.scoring import ScoreWeights
from aetheros.planetary.simulator import baseline_from_sites, simulate_sites


def plan_placements(
    workload: GlobalWorkload,
    sites: Sequence[PlacementSite],
    *,
    constraints: Sequence[PlanetaryConstraint] = (),
    weights: ScoreWeights | None = None,
    baseline: InfrastructureSnapshot | None = None,
    top_n: int = 5,
    now: datetime | None = None,
) -> ScheduleDecision:
    """Filter → score → twin-simulate → optimize → immutable decision."""

    if top_n < 1:
        raise ValueError("top_n must be >= 1")
    stamp = now or datetime.now(UTC)
    accepted, rejected = filter_candidates(workload, sites, constraints)
    if not accepted:
        return ScheduleDecision(
            workload=workload,
            best_candidate=None,
            alternatives=(),
            confidence=0.0,
            reasoning="No candidates survived constraints (simulation only).",
            simulations=(),
            rejected=rejected,
        )

    snap = baseline or baseline_from_sites(accepted, now=stamp)
    simulations = simulate_sites(workload, accepted, snap, now=stamp)
    candidates = evaluate_sites(
        workload,
        accepted,
        simulations,
        weights=weights,
    )
    sim_map = {s.site_id: s for s in simulations}
    refined = tuple(
        refine_score_with_simulation(c, sim_map[c.site_id])
        if c.site_id in sim_map
        else c
        for c in candidates
    )
    ranked = optimize_placements(refined, sites=accepted, top_n=top_n)

    best = ranked[0] if ranked else None
    twin_conf = (
        sum(s.twin_confidence for s in simulations) / len(simulations)
        if simulations
        else 0.0
    )
    depth_bonus = min(10.0, 2.0 * max(0, len(ranked) - 1))
    confidence = round(
        min(
            100.0,
            0.55 * (best.score if best else 0.0) + 0.35 * twin_conf + depth_bonus,
        ),
        2,
    )
    trade_bits = ", ".join(
        f"{c.site_id.split('/')[-1]}={c.trade_off}" for c in ranked[:3]
    )
    reasoning = (
        f"Recommended {best.site_id if best else '—'} "
        f"(score {best.score if best else 0:.1f}). "
        f"Trade-offs: {trade_bits or 'n/a'}. Status: Simulation Only."
    )
    return decision_from_ranked(
        workload,
        ranked,
        confidence=confidence,
        reasoning=reasoning,
        simulations=simulations,
        rejected=rejected,
    )


def demo_workload() -> GlobalWorkload:
    """Sample Global AI Inference workload (advice input only)."""

    return GlobalWorkload(
        id="wl-global-ai",
        name="Global AI Inference",
        cpu=28.0,
        memory=36.0,
        gpu=12.0,
        region_preference="eu-central-1",
        latency_target=25.0,
    )


def demo_sites() -> tuple[PlacementSite, ...]:
    """Differentiated planetary census across regions / DCs / clusters / nodes."""

    return (
        PlacementSite(
            region="eu-central-1",
            datacenter="fra-1",
            cluster="Beta-4",
            node="node-fra-a",
            cpu_available=72.0,
            memory_available=68.0,
            gpu_available=40.0,
            latency_ms=14.0,
            cluster_health=96.0,
            energy_efficiency=88.0,
            regional_resilience=94.0,
            compliance_tags=("gdpr", "eu-central-1"),
            metadata={"provider": "aws", "cost_index": "22"},
        ),
        PlacementSite(
            region="us-east-1",
            datacenter="iad-2",
            cluster="Alpha-1",
            node="node-iad-b",
            cpu_available=80.0,
            memory_available=75.0,
            gpu_available=55.0,
            latency_ms=22.0,
            cluster_health=91.0,
            energy_efficiency=70.0,
            regional_resilience=88.0,
            compliance_tags=("soc2", "us-east-1"),
            metadata={"provider": "aws", "cost_index": "35"},
        ),
        PlacementSite(
            region="ap-southeast-1",
            datacenter="sin-1",
            cluster="Gamma-2",
            node="node-sin-c",
            cpu_available=65.0,
            memory_available=70.0,
            gpu_available=30.0,
            latency_ms=38.0,
            cluster_health=89.0,
            energy_efficiency=82.0,
            regional_resilience=85.0,
            compliance_tags=("pdpa", "ap-southeast-1"),
            metadata={"provider": "gcp", "cost_index": "28"},
        ),
        PlacementSite(
            region="eu-west-1",
            datacenter="dub-1",
            cluster="Delta-3",
            node="node-dub-d",
            cpu_available=58.0,
            memory_available=62.0,
            gpu_available=20.0,
            latency_ms=18.0,
            cluster_health=93.0,
            energy_efficiency=91.0,
            regional_resilience=90.0,
            compliance_tags=("gdpr", "eu-west-1"),
            metadata={"provider": "azure", "cost_index": "18"},
        ),
        PlacementSite(
            region="us-west-2",
            datacenter="pdx-1",
            cluster="Epsilon-5",
            node="node-pdx-e",
            cpu_available=90.0,
            memory_available=85.0,
            gpu_available=60.0,
            latency_ms=30.0,
            cluster_health=87.0,
            energy_efficiency=65.0,
            regional_resilience=92.0,
            compliance_tags=("soc2", "us-west-2"),
            metadata={"provider": "aws", "cost_index": "40"},
        ),
        PlacementSite(
            region="eu-central-1",
            datacenter="fra-2",
            cluster="Beta-4",
            node="node-fra-f",
            cpu_available=40.0,
            memory_available=45.0,
            gpu_available=8.0,
            latency_ms=16.0,
            cluster_health=70.0,
            energy_efficiency=60.0,
            regional_resilience=75.0,
            degraded=True,
            compliance_tags=("gdpr", "eu-central-1"),
            metadata={"provider": "kubernetes", "cost_index": "15"},
        ),
    )


def demo_constraints() -> tuple[PlanetaryConstraint, ...]:
    """Default demo constraint set for dashboard / tests."""

    return (
        PlanetaryConstraint("AVOID_DEGRADED"),
        PlanetaryConstraint("LATENCY_MAX", 40.0),
        PlanetaryConstraint("REQUIRE_GPU", 10.0),
    )


def run_planetary_scheduler(
    workload: GlobalWorkload | None = None,
    sites: Sequence[PlacementSite] | None = None,
    *,
    constraints: Sequence[PlanetaryConstraint] | None = None,
    weights: ScoreWeights | None = None,
    top_n: int = 5,
    now: datetime | None = None,
) -> ScheduleDecision:
    """Convenience entry: demo defaults → full planetary recommendation."""

    return plan_placements(
        workload or demo_workload(),
        sites if sites is not None else demo_sites(),
        constraints=constraints if constraints is not None else demo_constraints(),
        weights=weights,
        top_n=top_n,
        now=now,
    )
