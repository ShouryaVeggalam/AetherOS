"""Distributed Scheduler — v4.0 P3 simulation-only placement recommendations.

Scores and ranks nodes using Digital Twin clones. Never executes workloads.
No SSH · no Kubernetes · no Docker APIs.
"""

from __future__ import annotations

from aetheros.scheduler.constraints import check_constraints, filter_candidates
from aetheros.scheduler.evaluator import evaluate_schedule, run_scheduler
from aetheros.scheduler.formatter import SchedulerPanel
from aetheros.scheduler.models import (
    NodeCapacity,
    ScheduleConstraint,
    SchedulePlan,
    ScheduleResult,
    TradeOff,
    Workload,
)
from aetheros.scheduler.planner import (
    capacities_from_topology_heartbeats,
    demo_nodes,
    demo_workload,
    plan_placements,
)
from aetheros.scheduler.scoring import ScoreWeights, score_node
from aetheros.scheduler.simulator import (
    simulate_plan,
    simulate_plans,
    synthetic_baseline_from_capacity,
)

__all__ = [
    "NodeCapacity",
    "ScheduleConstraint",
    "SchedulePlan",
    "ScheduleResult",
    "SchedulerPanel",
    "ScoreWeights",
    "TradeOff",
    "Workload",
    "capacities_from_topology_heartbeats",
    "check_constraints",
    "demo_nodes",
    "demo_workload",
    "evaluate_schedule",
    "filter_candidates",
    "plan_placements",
    "run_scheduler",
    "score_node",
    "simulate_plan",
    "simulate_plans",
    "synthetic_baseline_from_capacity",
]
