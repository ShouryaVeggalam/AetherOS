"""Schedule evaluator — compare simulated plans and pick a best recommendation.

Returns trade-offs, confidence, and reasoning. Never applies placements.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime

from aetheros.scheduler.models import (
    NodeCapacity,
    SchedulePlan,
    ScheduleResult,
    TradeOff,
)
from aetheros.scheduler.planner import plan_placements
from aetheros.scheduler.scoring import ScoreWeights
from aetheros.scheduler.simulator import simulate_plans
from aetheros.twin.models import TwinSnapshot


def evaluate_schedule(
    plans: Sequence[SchedulePlan],
    *,
    capacities: Mapping[str, NodeCapacity] | None = None,
    simulation_results: Sequence[object] = (),
    now: datetime | None = None,
) -> ScheduleResult:
    """Rank simulated plans and emit an immutable ``ScheduleResult``."""

    stamp = now or datetime.now(UTC)
    if not plans:
        return ScheduleResult(
            plans=(),
            cluster_health=0.0,
            predicted_latency=0.0,
            confidence=0.0,
            best_plan=None,
            trade_offs=(),
            rejected=(),
            created_at=stamp,
        )

    ranked = sorted(plans, key=lambda p: (-p.score, p.target_node))
    best = ranked[0]
    trade_offs = _trade_offs(best, ranked[1:])

    healths = []
    if capacities:
        for plan in ranked:
            node = capacities.get(plan.target_node)
            if node is not None:
                healths.append(node.cluster_health)
    cluster_health = round(sum(healths) / len(healths), 2) if healths else best.score

    # Confidence blends score, twin stability signals, and candidate depth.
    twin_conf = 0.0
    if simulation_results:
        twin_conf = sum(
            float(getattr(r, "confidence", 0.0)) for r in simulation_results
        ) / len(simulation_results)
        # Twin confidence often 0–1 or 0–100; normalize to 0–100.
        if twin_conf <= 1.0:
            twin_conf *= 100.0
    depth_bonus = min(10.0, 3.0 * max(0, len(ranked) - 1))
    confidence = round(
        min(100.0, 0.55 * best.score + 0.35 * twin_conf + depth_bonus),
        2,
    )

    return ScheduleResult(
        plans=tuple(ranked),
        cluster_health=cluster_health,
        predicted_latency=best.predicted_latency_ms,
        confidence=confidence,
        best_plan=best,
        trade_offs=trade_offs,
        rejected=(),
        created_at=stamp,
    )


def run_scheduler(
    workload: object,
    nodes: Sequence[NodeCapacity],
    *,
    constraints: Sequence[object] = (),
    weights: ScoreWeights | None = None,
    baseline: TwinSnapshot | None = None,
    top_n: int = 3,
    now: datetime | None = None,
) -> ScheduleResult:
    """End-to-end: constrain → score → twin-simulate → evaluate."""

    from aetheros.scheduler.models import ScheduleConstraint, Workload
    from aetheros.scheduler.simulator import synthetic_baseline_from_capacity

    if not isinstance(workload, Workload):
        raise TypeError("workload must be a Workload")
    constr = tuple(c for c in constraints if isinstance(c, ScheduleConstraint))
    plans, rejected = plan_placements(
        workload,
        nodes,
        constraints=constr,
        weights=weights,
        top_n=top_n,
    )
    cap_map = {n.node_id: n for n in nodes}
    sim_results: tuple[object, ...] = ()
    if plans:
        if baseline is None:
            # Use best unscored capacity as twin seed (cloned later).
            seed_node = cap_map.get(plans[0].target_node) or nodes[0]
            baseline = synthetic_baseline_from_capacity(seed_node, now=now)
        plans, sim_results = simulate_plans(plans, cap_map, baseline, now=now)
    result = evaluate_schedule(
        plans,
        capacities=cap_map,
        simulation_results=sim_results,
        now=now,
    )
    return ScheduleResult(
        plans=result.plans,
        cluster_health=result.cluster_health,
        predicted_latency=result.predicted_latency,
        confidence=result.confidence,
        best_plan=result.best_plan,
        trade_offs=result.trade_offs,
        rejected=rejected,
        created_at=result.created_at,
    )


def _trade_offs(
    best: SchedulePlan,
    others: Sequence[SchedulePlan],
) -> tuple[TradeOff, ...]:
    out: list[TradeOff] = []
    for alt in others[:3]:
        delta = round(best.score - alt.score, 2)
        summary = (
            f"{best.target_node} leads {alt.target_node} by {delta:.1f} pts "
            f"(cpu {best.predicted_cpu:.0f}% vs {alt.predicted_cpu:.0f}%, "
            f"lat {best.predicted_latency_ms:.1f} vs {alt.predicted_latency_ms:.1f} ms)"
        )
        out.append(
            TradeOff(
                versus_node=alt.target_node,
                summary=summary,
                score_delta=delta,
            )
        )
    return tuple(out)
