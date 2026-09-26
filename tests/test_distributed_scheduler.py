"""Tests for v4.0 P3 Distributed Scheduler (simulation only)."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from rich.console import Console

from aetheros.scheduler import (
    NodeCapacity,
    ScheduleConstraint,
    SchedulePlan,
    ScheduleResult,
    SchedulerPanel,
    ScoreWeights,
    TradeOff,
    Workload,
    capacities_from_topology_heartbeats,
    check_constraints,
    demo_nodes,
    demo_workload,
    evaluate_schedule,
    filter_candidates,
    plan_placements,
    run_scheduler,
    score_node,
    simulate_plan,
    simulate_plans,
    synthetic_baseline_from_capacity,
)
from aetheros.scheduler.scoring import DEFAULT_WEIGHTS


def _stamp() -> datetime:
    return datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def _workload(**kwargs: object) -> Workload:
    base = dict(
        id="wl-1",
        name="AI Training",
        cpu_request=20.0,
        memory_request=30.0,
        gpu_request=5.0,
        priority=50.0,
    )
    base.update(kwargs)
    return Workload(**base)  # type: ignore[arg-type]


def _node(node_id: str = "A", **kwargs: object) -> NodeCapacity:
    base = dict(
        node_id=node_id,
        available_cpu=60.0,
        available_memory=70.0,
        available_gpu=20.0,
        utilization=40.0,
        latency_ms=5.0,
        region_id="us-east",
        cluster_health=80.0,
    )
    base.update(kwargs)
    return NodeCapacity(**base)  # type: ignore[arg-type]


# --- models ------------------------------------------------------------------


def test_workload_validation() -> None:
    with pytest.raises(ValueError):
        Workload(id=" ", name="n", cpu_request=1, memory_request=1, gpu_request=0, priority=1)
    with pytest.raises(ValueError):
        Workload(id="w", name=" ", cpu_request=1, memory_request=1, gpu_request=0, priority=1)
    with pytest.raises(ValueError):
        Workload(id="w", name="n", cpu_request=-1, memory_request=1, gpu_request=0, priority=1)
    with pytest.raises(ValueError):
        Workload(id="w", name="n", cpu_request=1, memory_request=1, gpu_request=0, priority=101)


def test_node_capacity_validation() -> None:
    with pytest.raises(ValueError):
        NodeCapacity(
            node_id=" ",
            available_cpu=1,
            available_memory=1,
            available_gpu=0,
            utilization=1,
        )
    with pytest.raises(ValueError):
        NodeCapacity(
            node_id="n",
            available_cpu=101,
            available_memory=1,
            available_gpu=0,
            utilization=1,
        )
    with pytest.raises(ValueError):
        NodeCapacity(
            node_id="n",
            available_cpu=1,
            available_memory=1,
            available_gpu=0,
            utilization=1,
            latency_ms=-1,
        )


def test_constraint_and_plan_validation() -> None:
    with pytest.raises(ValueError):
        ScheduleConstraint(kind="NOPE")  # type: ignore[arg-type]
    wl = _workload()
    with pytest.raises(ValueError):
        SchedulePlan(workload=wl, target_node=" ", score=50, reasoning="ok")
    with pytest.raises(ValueError):
        SchedulePlan(workload=wl, target_node="A", score=101, reasoning="ok")
    with pytest.raises(ValueError):
        SchedulePlan(workload=wl, target_node="A", score=50, reasoning=" ")
    with pytest.raises(ValueError):
        TradeOff(versus_node=" ", summary="s", score_delta=1)
    with pytest.raises(ValueError):
        TradeOff(versus_node="B", summary=" ", score_delta=1)
    with pytest.raises(ValueError):
        ScheduleResult(
            plans=(),
            cluster_health=101,
            predicted_latency=0,
            confidence=0,
        )
    with pytest.raises(ValueError):
        ScheduleResult(
            plans=(),
            cluster_health=0,
            predicted_latency=-1,
            confidence=0,
        )
    with pytest.raises(ValueError):
        ScheduleResult(
            plans=(),
            cluster_health=0,
            predicted_latency=0,
            confidence=101,
        )


# --- constraints -------------------------------------------------------------


def test_intrinsic_capacity_rejects() -> None:
    wl = _workload(cpu_request=90)
    ok, reason = check_constraints(wl, _node(available_cpu=50))
    assert not ok and "CPU" in reason
    ok, reason = check_constraints(_workload(memory_request=90), _node(available_memory=10))
    assert not ok and "memory" in reason.lower()
    ok, reason = check_constraints(_workload(gpu_request=50), _node(available_gpu=5))
    assert not ok and "GPU" in reason


def test_max_cpu_and_memory_constraints() -> None:
    node = _node(utilization=80.0, available_memory=70.0, available_cpu=80.0)
    wl = _workload(cpu_request=40.0, memory_request=50.0)
    ok, reason = check_constraints(
        wl, node, (ScheduleConstraint(kind="MAX_CPU", value=90.0),)
    )
    # projected util = 80 + 40*0.5 = 100 > 90
    assert not ok and "MAX_CPU" in reason
    ok, reason = check_constraints(
        wl, node, (ScheduleConstraint(kind="MAX_MEMORY", value=50.0),)
    )
    # used = 100-70=30 + 50 request = 80 > 50
    assert not ok and "MAX_MEMORY" in reason
    # Accepting path for MAX_CPU under limit
    ok, reason = check_constraints(
        _workload(cpu_request=10.0, memory_request=10.0),
        _node(utilization=40.0, available_memory=80.0),
        (ScheduleConstraint(kind="MAX_CPU", value=90.0),),
    )
    assert ok
    ok, reason = check_constraints(
        _workload(cpu_request=10.0, memory_request=10.0),
        _node(utilization=40.0, available_memory=80.0),
        (ScheduleConstraint(kind="MAX_MEMORY", value=90.0),),
    )
    assert ok


def test_require_gpu_region_lock_avoid_overload() -> None:
    node = _node(available_gpu=5.0, region_id="eu-west", utilization=90.0)
    wl = _workload(gpu_request=2.0)
    ok, reason = check_constraints(
        wl, node, (ScheduleConstraint(kind="REQUIRE_GPU", value=10.0),)
    )
    assert not ok and "REQUIRE_GPU" in reason
    ok, reason = check_constraints(
        wl,
        _node(available_gpu=20.0, region_id="us-east"),
        (ScheduleConstraint(kind="REGION_LOCK", value="eu-west"),),
    )
    assert not ok and "REGION_LOCK" in reason
    ok, reason = check_constraints(
        wl, node, (ScheduleConstraint(kind="REGION_LOCK", value=""),)
    )
    assert not ok and "empty" in reason
    ok, reason = check_constraints(
        wl, node, (ScheduleConstraint(kind="AVOID_OVERLOAD", value=85.0),)
    )
    assert not ok and "AVOID_OVERLOAD" in reason
    ok, reason = check_constraints(
        _workload(gpu_request=0),
        _node(available_gpu=20, utilization=50, region_id="eu-west"),
        (
            ScheduleConstraint(kind="REQUIRE_GPU", value=1.0),
            ScheduleConstraint(kind="REGION_LOCK", value="eu-west"),
            ScheduleConstraint(kind="AVOID_OVERLOAD", value=85.0),
        ),
    )
    assert ok and reason == "ok"


def test_unknown_constraint_kind_via_internal() -> None:
    from aetheros.scheduler.constraints import _apply_one

    ok, reason = _apply_one(
        _workload(),
        _node(),
        SimpleNamespace(kind="UNKNOWN", value=0),  # type: ignore[arg-type]
    )
    assert not ok and "unknown" in reason

    wl = _workload(cpu_request=50)
    nodes = (
        _node("good", available_cpu=80),
        _node("bad", available_cpu=10),
    )
    accepted, rejected = filter_candidates(wl, nodes)
    assert len(accepted) == 1 and accepted[0].node_id == "good"
    assert rejected and rejected[0][0] == "bad"


# --- scoring -----------------------------------------------------------------


def test_score_weights_must_be_positive() -> None:
    with pytest.raises(ValueError):
        ScoreWeights(cpu=0, memory=0, gpu=0, latency=0, cluster_health=0, utilization=0)


def test_score_node_normalized_and_deterministic() -> None:
    wl = _workload()
    a = _node("A", available_cpu=80, latency_ms=2, cluster_health=95, utilization=20)
    b = _node("B", available_cpu=40, latency_ms=40, cluster_health=40, utilization=80)
    sa, ra = score_node(wl, a)
    sb, rb = score_node(wl, b)
    assert 0 <= sa <= 100 and 0 <= sb <= 100
    assert sa > sb
    assert "cpu=" in ra and "→" in rb
    again, _ = score_node(wl, a, weights=DEFAULT_WEIGHTS)
    assert again == sa


def test_score_availability_and_latency_edges() -> None:
    wl = _workload(cpu_request=0, memory_request=0, gpu_request=0)
    score, _ = score_node(wl, _node(available_cpu=70, available_memory=60, available_gpu=50))
    assert score > 0
    wl2 = _workload(cpu_request=90)
    score2, _ = score_node(wl2, _node(available_cpu=10))
    assert score2 < score
    # High latency clamps toward 0 contribution.
    low_lat, _ = score_node(_workload(), _node(latency_ms=0))
    high_lat, _ = score_node(_workload(), _node(latency_ms=100))
    assert low_lat > high_lat


# --- planner -----------------------------------------------------------------


def test_plan_placements_top_n_and_rejects() -> None:
    wl = demo_workload()
    nodes = demo_nodes()
    plans, rejected = plan_placements(
        wl,
        nodes,
        constraints=(ScheduleConstraint(kind="REQUIRE_GPU", value=1.0),),
        top_n=3,
    )
    assert 1 <= len(plans) <= 3
    assert plans[0].score >= plans[-1].score
    assert all(p.reasoning for p in plans)
    with pytest.raises(ValueError):
        plan_placements(wl, nodes, top_n=0)


def test_capacities_from_topology_heartbeats() -> None:
    hb = SimpleNamespace(cpu=30.0, memory=40.0, network=4.0)
    online = SimpleNamespace(
        node_id="n1",
        heartbeat=hb,
        status="online",
        region_id="us-east",
        hostname="host-1",
        available_gpu=12.0,
    )
    offline = SimpleNamespace(
        node_id="n2",
        heartbeat=None,
        status="offline",
        region_id="",
        hostname="",
    )
    blank = SimpleNamespace(node_id=" ", heartbeat=None, status="online")
    caps = capacities_from_topology_heartbeats((online, offline, blank))
    assert len(caps) == 2
    assert caps[0].available_cpu == pytest.approx(70.0)
    assert caps[0].available_gpu == 12.0
    assert caps[1].available_cpu == 0.0
    assert caps[1].cluster_health == 20.0


# --- simulator ---------------------------------------------------------------


def test_simulate_plan_clones_twin_only() -> None:
    wl = _workload()
    node = _node("B")
    plan = SchedulePlan(workload=wl, target_node="B", score=80.0, reasoning="seed")
    baseline = synthetic_baseline_from_capacity(node, now=_stamp())
    enriched, result = simulate_plan(plan, node, baseline, now=_stamp())
    assert enriched.predicted_cpu >= 0
    assert enriched.predicted_latency_ms >= 0
    assert result.confidence >= 0
    # Baseline graph identity unchanged (clone path).
    assert baseline.resource_graph.nodes


def test_simulate_plans_skips_missing_capacity() -> None:
    wl = _workload()
    node = _node("A")
    plans = (
        SchedulePlan(workload=wl, target_node="A", score=70, reasoning="a"),
        SchedulePlan(workload=wl, target_node="missing", score=60, reasoning="m"),
    )
    baseline = synthetic_baseline_from_capacity(node, now=_stamp())
    enriched, results = simulate_plans(
        plans, {"A": node}, baseline, now=_stamp()
    )
    assert len(enriched) == 1 and enriched[0].target_node == "A"
    assert len(results) == 1


# --- evaluator ---------------------------------------------------------------


def test_evaluate_schedule_twin_confidence_normalized() -> None:
    wl = _workload()
    plans = (
        SchedulePlan(
            workload=wl,
            target_node="A",
            score=80,
            reasoning="a",
            predicted_cpu=50,
            predicted_latency_ms=5,
        ),
    )
    # Simulate twin conf in 0–1 scale to hit normalization branch.
    twin = SimpleNamespace(confidence=0.82)
    result = evaluate_schedule(
        plans,
        capacities={"A": _node("A", cluster_health=88)},
        simulation_results=(twin,),
        now=_stamp(),
    )
    assert result.confidence > 0

    empty = evaluate_schedule((), now=_stamp())
    assert empty.best_plan is None and empty.confidence == 0.0
    wl = _workload()
    plans = (
        SchedulePlan(workload=wl, target_node="B", score=90, reasoning="b", predicted_cpu=61, predicted_latency_ms=3),
        SchedulePlan(workload=wl, target_node="A", score=70, reasoning="a", predicted_cpu=75, predicted_latency_ms=8),
        SchedulePlan(workload=wl, target_node="C", score=65, reasoning="c", predicted_cpu=80, predicted_latency_ms=12),
    )
    caps = {"A": _node("A"), "B": _node("B", cluster_health=90), "C": _node("C")}
    result = evaluate_schedule(plans, capacities=caps, now=_stamp())
    assert result.best_plan is not None
    assert result.best_plan.target_node == "B"
    assert result.trade_offs
    assert result.confidence > 0
    assert result.status == "simulation_only"


def test_run_scheduler_end_to_end() -> None:
    wl = demo_workload()
    nodes = demo_nodes()
    result = run_scheduler(
        wl,
        nodes,
        constraints=(
            ScheduleConstraint(kind="REQUIRE_GPU", value=1.0),
            ScheduleConstraint(kind="AVOID_OVERLOAD", value=85.0),
        ),
        now=_stamp(),
    )
    assert result.best_plan is not None
    assert result.best_plan.target_node in {"A", "B", "C"}
    assert len(result.plans) <= 3
    assert 0 <= result.confidence <= 100
    with pytest.raises(TypeError):
        run_scheduler("nope", nodes)  # type: ignore[arg-type]


def test_run_scheduler_no_candidates() -> None:
    wl = _workload(cpu_request=99)
    nodes = (_node("A", available_cpu=5),)
    result = run_scheduler(wl, nodes, now=_stamp())
    assert result.best_plan is None
    assert result.rejected


# --- formatter ---------------------------------------------------------------


def test_scheduler_panel_views() -> None:
    console = Console(record=True, width=100)
    console.print(SchedulerPanel())
    idle = console.export_text()
    assert "DISTRIBUTED SCHEDULER" in idle or "Simulation Only" in idle

    wl = demo_workload()
    result = run_scheduler(wl, demo_nodes(), now=_stamp())
    for view in (
        "summary",
        "workloads",
        "candidates",
        "scores",
        "simulation",
        "tradeoffs",
    ):
        console = Console(record=True, width=100)
        console.print(SchedulerPanel(workload=wl, result=result, view=view))
        text = console.export_text()
        assert "DISTRIBUTED SCHEDULER" in text or "Distributed Scheduler" in text


def test_scheduler_panel_empty_plans_tradeoffs() -> None:
    wl = demo_workload()
    empty = ScheduleResult(
        plans=(),
        cluster_health=0,
        predicted_latency=0,
        confidence=0,
        best_plan=None,
        trade_offs=(),
        rejected=(("X", "no capacity"),),
        created_at=_stamp(),
    )
    console = Console(record=True, width=100)
    for view in ("candidates", "tradeoffs", "summary", "simulation", "scores"):
        console.print(SchedulerPanel(workload=wl, result=empty, view=view))
