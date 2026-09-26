"""Planetary evaluator — blend scores with twin simulations into candidates.

Produces enriched ``Candidate`` rows with latency / availability from the
Infrastructure Digital Twin. Never applies placements.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from aetheros.planetary.models import (
    Candidate,
    GlobalWorkload,
    PlacementSimulation,
    PlacementSite,
)
from aetheros.planetary.scoring import ScoreWeights, score_site


def evaluate_candidate(
    workload: GlobalWorkload,
    site: PlacementSite,
    simulation: PlacementSimulation | None = None,
    *,
    weights: ScoreWeights | None = None,
) -> Candidate:
    """Score one site and optionally overlay twin simulation metrics."""

    score, reasoning = score_site(workload, site, weights=weights)
    latency = simulation.latency_ms if simulation is not None else site.latency_ms
    availability = (
        simulation.availability if simulation is not None else site.cluster_health
    )
    if simulation is not None:
        reasoning = (
            f"{reasoning} | twin lat={simulation.latency_ms:.1f}ms "
            f"avail={simulation.availability:.2f}% "
            f"resilience={simulation.failure_resilience:.1f}"
        )
    return Candidate(
        region=site.region,
        datacenter=site.datacenter,
        cluster=site.cluster,
        node=site.node,
        score=score,
        latency_ms=round(latency, 2),
        availability=round(availability, 2),
        reasoning=reasoning,
    )


def evaluate_sites(
    workload: GlobalWorkload,
    sites: Sequence[PlacementSite],
    simulations: Sequence[PlacementSimulation] = (),
    *,
    weights: ScoreWeights | None = None,
) -> tuple[Candidate, ...]:
    """Evaluate every site; attach matching simulations by site_id."""

    sim_map: Mapping[str, PlacementSimulation] = {s.site_id: s for s in simulations}
    out: list[Candidate] = []
    for site in sites:
        out.append(
            evaluate_candidate(
                workload,
                site,
                sim_map.get(site.site_id),
                weights=weights,
            )
        )
    return tuple(out)


def refine_score_with_simulation(
    candidate: Candidate,
    simulation: PlacementSimulation,
) -> Candidate:
    """Deterministically nudge score using twin resilience / latency signals."""

    # Small, bounded adjustment — twin informs, does not invent winners.
    latency_adj = max(-3.0, min(3.0, (30.0 - simulation.latency_ms) / 20.0))
    resilience_adj = max(-2.0, min(2.0, (simulation.failure_resilience - 80.0) / 20.0))
    new_score = round(
        max(0.0, min(100.0, candidate.score + latency_adj + resilience_adj)), 2
    )
    return Candidate(
        region=candidate.region,
        datacenter=candidate.datacenter,
        cluster=candidate.cluster,
        node=candidate.node,
        score=new_score,
        latency_ms=simulation.latency_ms,
        availability=simulation.availability,
        reasoning=(
            f"{candidate.reasoning} | refined Δ={new_score - candidate.score:+.2f}"
        ),
        trade_off=candidate.trade_off,
    )
