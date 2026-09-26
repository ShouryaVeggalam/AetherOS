"""Tests for v6.0 P4 Planetary Scheduler (simulation only)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from rich.console import Console

from aetheros.planetary import (
    CONSTRAINT_KINDS,
    DEFAULT_WEIGHTS,
    Candidate,
    GlobalWorkload,
    PlacementSimulation,
    PlacementSite,
    PlanetaryConstraint,
    PlanetarySchedulerPanel,
    ScheduleDecision,
    ScoreWeights,
    baseline_from_sites,
    check_constraints,
    decision_from_ranked,
    demo_constraints,
    demo_sites,
    demo_workload,
    evaluate_candidate,
    evaluate_sites,
    explain_trade_offs,
    filter_candidates,
    optimize_placements,
    plan_placements,
    refine_score_with_simulation,
    run_planetary_scheduler,
    score_site,
    simulate_site,
    simulate_sites,
    twin_latency_probe,
)


def _stamp() -> datetime:
    return datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


def _workload(**kwargs: object) -> GlobalWorkload:
    base: dict[str, object] = dict(
        id="wl-1",
        name="Global AI Inference",
        cpu=20.0,
        memory=30.0,
        gpu=5.0,
        region_preference="eu-central-1",
        latency_target=25.0,
    )
    base.update(kwargs)
    return GlobalWorkload(**base)  # type: ignore[arg-type]


def _site(
    region: str = "eu-central-1",
    datacenter: str = "fra-1",
    cluster: str = "Beta-4",
    node: str = "node-a",
    **kwargs: object,
) -> PlacementSite:
    base: dict[str, object] = dict(
        region=region,
        datacenter=datacenter,
        cluster=cluster,
        node=node,
        cpu_available=70.0,
        memory_available=70.0,
        gpu_available=20.0,
        latency_ms=14.0,
        cluster_health=95.0,
        energy_efficiency=85.0,
        regional_resilience=90.0,
    )
    base.update(kwargs)
    return PlacementSite(**base)  # type: ignore[arg-type]


# --- models ------------------------------------------------------------------


def test_global_workload_validation() -> None:
    with pytest.raises(ValueError):
        GlobalWorkload(id=" ", name="n", cpu=1, memory=1)
    with pytest.raises(ValueError):
        GlobalWorkload(id="w", name=" ", cpu=1, memory=1)
    with pytest.raises(ValueError):
        GlobalWorkload(id="w", name="n", cpu=-1, memory=1)
    with pytest.raises(ValueError):
        GlobalWorkload(id="w", name="n", cpu=1, memory=1, latency_target=0)


def test_placement_site_and_candidate() -> None:
    site = _site()
    assert site.site_id == "eu-central-1/fra-1/Beta-4/node-a"
    with pytest.raises(ValueError):
        PlacementSite(
            region="",
            datacenter="d",
            cluster="c",
            node="n",
            cpu_available=1,
            memory_available=1,
        )
    cand = Candidate(
        region="eu-central-1",
        datacenter="fra-1",
        cluster="Beta-4",
        node="node-a",
        score=88.5,
        latency_ms=14.0,
        availability=99.5,
        reasoning="ok",
        trade_off="Best latency",
    )
    assert cand.site_id.endswith("node-a")
    assert cand.to_dict()["score"] == 88.5
    with pytest.raises(ValueError):
        Candidate(region="r", datacenter="d", cluster="c", node="n", score=101.0)


def test_constraint_kinds_and_decision() -> None:
    assert "REGION_LOCK" in CONSTRAINT_KINDS
    with pytest.raises(ValueError):
        PlanetaryConstraint("MAX_CPU")  # type: ignore[arg-type]
    wl = _workload()
    decision = ScheduleDecision(
        workload=wl,
        best_candidate=None,
        alternatives=(),
        confidence=0.0,
        reasoning="none",
    )
    assert decision.to_dict()["best_candidate"] is None
    sim = PlacementSimulation(
        site_id="a/b/c/d",
        latency_ms=10.0,
        availability=99.0,
        cpu=40.0,
        memory=42.0,
        failure_resilience=88.0,
    )
    assert sim.to_dict()["availability"] == 99.0
    with pytest.raises(ValueError):
        PlacementSimulation(
            site_id=" ",
            latency_ms=1,
            availability=1,
            cpu=1,
            memory=1,
            failure_resilience=1,
        )


def test_workload_to_dict() -> None:
    assert _workload().to_dict()["name"] == "Global AI Inference"


# --- constraints -------------------------------------------------------------


def test_intrinsic_capacity_rejects() -> None:
    wl = _workload(cpu=90.0)
    site = _site(cpu_available=50.0)
    ok, reason = check_constraints(wl, site)
    assert not ok
    assert "CPU" in reason


def test_region_lock_and_latency_max() -> None:
    wl = _workload()
    site = _site(region="us-east-1", latency_ms=50.0)
    ok, reason = check_constraints(
        wl, site, (PlanetaryConstraint("REGION_LOCK", "eu-central-1"),)
    )
    assert not ok
    assert "REGION_LOCK" in reason
    ok2, reason2 = check_constraints(
        wl, site, (PlanetaryConstraint("LATENCY_MAX", 40.0),)
    )
    assert not ok2
    assert "LATENCY_MAX" in reason2


def test_require_gpu_avoid_degraded_energy_compliance() -> None:
    wl = _workload(gpu=15.0)
    site = _site(gpu_available=5.0, degraded=True, energy_efficiency=50.0)
    ok, _ = check_constraints(wl, site, (PlanetaryConstraint("REQUIRE_GPU", 10.0),))
    assert not ok
    site2 = _site(degraded=True)
    ok2, reason2 = check_constraints(
        wl, site2, (PlanetaryConstraint("AVOID_DEGRADED"),)
    )
    assert not ok2
    assert "DEGRADED" in reason2
    site3 = _site(energy_efficiency=60.0)
    ok3, reason3 = check_constraints(
        wl, site3, (PlanetaryConstraint("ENERGY_PRIORITY", 75.0),)
    )
    assert not ok3
    assert "ENERGY" in reason3
    site4 = _site(compliance_tags=("soc2",))
    ok4, reason4 = check_constraints(
        wl, site4, (PlanetaryConstraint("COMPLIANCE_REGION", "gdpr"),)
    )
    assert not ok4
    assert "COMPLIANCE" in reason4
    site5 = _site(compliance_tags=("gdpr",), region="eu-central-1")
    ok5, _ = check_constraints(
        wl, site5, (PlanetaryConstraint("COMPLIANCE_REGION", "gdpr"),)
    )
    assert ok5


def test_memory_reject_and_constraint_success_paths() -> None:
    wl = _workload(memory=90.0, gpu=2.0)
    site = _site(memory_available=10.0, gpu_available=20.0, energy_efficiency=90.0)
    ok, reason = check_constraints(wl, site)
    assert not ok and "memory" in reason.lower()
    wl2 = _workload(gpu=2.0)
    site2 = _site(gpu_available=20.0, energy_efficiency=90.0, compliance_tags=("gdpr",))
    ok2, _ = check_constraints(
        wl2,
        site2,
        (
            PlanetaryConstraint("REQUIRE_GPU", ""),
            PlanetaryConstraint("ENERGY_PRIORITY", ""),
            PlanetaryConstraint("LATENCY_MAX", ""),
            PlanetaryConstraint("COMPLIANCE_REGION", "eu-central-1"),
        ),
    )
    assert ok2
    ok3, reason3 = check_constraints(
        wl2, site2, (PlanetaryConstraint("COMPLIANCE_REGION", " "),)
    )
    assert not ok3 and "empty" in reason3


def test_model_edge_validations() -> None:
    with pytest.raises(ValueError):
        PlacementSite(
            region="r",
            datacenter="d",
            cluster="c",
            node="n",
            cpu_available=-1.0,
            memory_available=1.0,
        )
    with pytest.raises(ValueError):
        PlacementSite(
            region="r",
            datacenter="d",
            cluster="c",
            node="n",
            cpu_available=1.0,
            memory_available=1.0,
            latency_ms=-1.0,
        )
    with pytest.raises(ValueError):
        Candidate(
            region="r",
            datacenter="d",
            cluster="c",
            node="n",
            score=50.0,
            latency_ms=-1.0,
        )
    with pytest.raises(ValueError):
        Candidate(
            region="r",
            datacenter="d",
            cluster="c",
            node="n",
            score=50.0,
            availability=101.0,
        )
    with pytest.raises(ValueError):
        PlacementSimulation(
            site_id="a/b/c/d",
            latency_ms=-1.0,
            availability=1,
            cpu=1,
            memory=1,
            failure_resilience=1,
        )
    with pytest.raises(ValueError):
        PlacementSimulation(
            site_id="a/b/c/d",
            latency_ms=1.0,
            availability=101.0,
            cpu=1,
            memory=1,
            failure_resilience=1,
        )
    with pytest.raises(ValueError):
        ScheduleDecision(
            workload=_workload(),
            best_candidate=None,
            alternatives=(),
            confidence=101.0,
            reasoning="x",
        )


def test_naive_datetime_simulator_paths() -> None:
    wl = _workload()
    site = _site()
    naive = datetime(2026, 9, 26, 12, 0)
    baseline = baseline_from_sites((site,), now=naive)
    sim = simulate_site(wl, site, baseline, now=naive)
    assert sim.latency_ms >= 0.0


def test_optimizer_no_site_map_labels() -> None:
    cands = (
        Candidate(
            region="r1",
            datacenter="d",
            cluster="c",
            node="n1",
            score=90.0,
            latency_ms=5.0,
            availability=99.0,
        ),
        Candidate(
            region="r2",
            datacenter="d",
            cluster="c",
            node="n2",
            score=80.0,
            latency_ms=20.0,
            availability=95.0,
        ),
    )
    ranked = optimize_placements(cands, sites=(), top_n=2)
    assert ranked[0].trade_off
    # Second without specialist site map still labeled.
    assert ranked[1].trade_off


def test_filter_candidates_splits() -> None:
    wl = _workload(gpu=10.0)
    sites = (
        _site(node="good", gpu_available=20.0),
        _site(node="bad", gpu_available=1.0, region="us-east-1"),
    )
    accepted, rejected = filter_candidates(
        wl,
        sites,
        (
            PlanetaryConstraint("REQUIRE_GPU", 8.0),
            PlanetaryConstraint("REGION_LOCK", "eu-central-1"),
        ),
    )
    assert len(accepted) == 1
    assert accepted[0].node == "good"
    assert rejected


def test_empty_region_lock_and_unknown() -> None:
    wl = _workload()
    site = _site()
    ok, reason = check_constraints(wl, site, (PlanetaryConstraint("REGION_LOCK", " "),))
    assert not ok
    assert "empty" in reason
    # Bypass model validation to hit unknown-kind branch in _apply_one.
    bogus = PlanetaryConstraint.__new__(PlanetaryConstraint)
    object.__setattr__(bogus, "kind", "MAX_CPU")
    object.__setattr__(bogus, "value", 1.0)
    ok2, reason2 = check_constraints(wl, site, (bogus,))
    assert not ok2
    assert "unknown" in reason2


# --- scoring -----------------------------------------------------------------


def test_score_site_normalized_and_deterministic() -> None:
    wl = _workload()
    site = _site()
    a, ra = score_site(wl, site)
    b, rb = score_site(wl, site)
    assert a == b
    assert 0.0 <= a <= 100.0
    assert "cpu=" in ra
    assert ra == rb


def test_score_prefers_headroom_and_region() -> None:
    wl = _workload(region_preference="eu-central-1")
    rich = _site(cpu_available=90.0, memory_available=90.0, latency_ms=10.0)
    poor = _site(
        region="us-east-1",
        datacenter="iad",
        cluster="A",
        node="x",
        cpu_available=25.0,
        memory_available=25.0,
        latency_ms=80.0,
        cluster_health=50.0,
        energy_efficiency=40.0,
        regional_resilience=40.0,
    )
    assert score_site(wl, rich)[0] > score_site(wl, poor)[0]


def test_score_weights_validation_and_zero_gpu() -> None:
    with pytest.raises(ValueError):
        ScoreWeights(
            cpu=0,
            memory=0,
            gpu=0,
            latency=0,
            cluster_health=0,
            energy_efficiency=0,
            regional_resilience=0,
        )
    wl = _workload(gpu=0.0)
    score, _ = score_site(wl, _site(gpu_available=0.0), weights=DEFAULT_WEIGHTS)
    assert 0.0 <= score <= 100.0


def test_score_insufficient_capacity_zeros_metric() -> None:
    wl = _workload(cpu=100.0)
    site = _site(cpu_available=10.0)
    # Still callable; CPU component contributes 0 — overall may be low.
    score, reasoning = score_site(wl, site)
    assert "cpu=0" in reasoning
    assert score < 90.0


# --- simulator ---------------------------------------------------------------


def test_simulate_site_read_only() -> None:
    wl = _workload()
    sites = demo_sites()[:3]
    baseline = baseline_from_sites(sites, now=_stamp())
    before_ids = [n.id for n in baseline.topology]
    sims = simulate_sites(wl, sites, baseline, now=_stamp())
    assert len(sims) == 3
    assert all(isinstance(s, PlacementSimulation) for s in sims)
    assert [n.id for n in baseline.topology] == before_ids
    probe = twin_latency_probe(baseline)
    assert probe >= 0.0
    one = simulate_site(wl, sites[0], baseline, now=_stamp())
    assert one.site_id == sites[0].site_id


def test_baseline_from_empty_falls_back() -> None:
    snap = baseline_from_sites((), now=_stamp())
    assert snap.node_count >= 1


# --- evaluator ---------------------------------------------------------------


def test_evaluate_candidate_and_refine() -> None:
    wl = _workload()
    site = _site()
    cand = evaluate_candidate(wl, site)
    assert 0.0 <= cand.score <= 100.0
    sim = PlacementSimulation(
        site_id=site.site_id,
        latency_ms=12.0,
        availability=99.9,
        cpu=40.0,
        memory=41.0,
        failure_resilience=92.0,
        twin_confidence=90.0,
    )
    enriched = evaluate_candidate(wl, site, sim)
    assert "twin lat=" in enriched.reasoning
    refined = refine_score_with_simulation(enriched, sim)
    assert refined.latency_ms == 12.0
    batch = evaluate_sites(wl, (site,), (sim,))
    assert len(batch) == 1


# --- optimizer ---------------------------------------------------------------


def test_optimize_top5_deterministic_tradeoffs() -> None:
    sites = demo_sites()
    wl = demo_workload()
    cands = evaluate_sites(wl, sites)
    a = optimize_placements(cands, sites=sites, top_n=5)
    b = optimize_placements(cands, sites=sites, top_n=5)
    assert a == b
    assert len(a) <= 5
    assert any(c.trade_off for c in a)
    lines = explain_trade_offs(a)
    assert lines and lines[0].startswith("Candidate A")
    with pytest.raises(ValueError):
        optimize_placements(cands, top_n=0)
    assert optimize_placements(()) == ()


def test_decision_from_ranked() -> None:
    wl = demo_workload()
    ranked = optimize_placements(evaluate_sites(wl, demo_sites()[:3]), top_n=3)
    decision = decision_from_ranked(
        wl,
        ranked,
        confidence=90.0,
        reasoning="test",
    )
    assert decision.best_candidate is not None
    assert len(decision.alternatives) == max(0, len(ranked) - 1)
    with pytest.raises(TypeError):
        decision_from_ranked("bad", ranked, confidence=1.0, reasoning="x")  # type: ignore[arg-type]


# --- planner / end-to-end ----------------------------------------------------


def test_plan_placements_end_to_end() -> None:
    decision = plan_placements(
        demo_workload(),
        demo_sites(),
        constraints=demo_constraints(),
        now=_stamp(),
    )
    assert decision.best_candidate is not None
    assert decision.confidence > 0
    assert "Simulation Only" in decision.reasoning
    assert decision.simulations
    # Degraded / under-capacity fra-f should appear in rejects.
    assert decision.rejected
    assert any("node-fra-f" in r[0] for r in decision.rejected)


def test_plan_no_candidates() -> None:
    wl = _workload(cpu=99.0, gpu=99.0)
    decision = plan_placements(
        wl,
        (_site(cpu_available=1.0, gpu_available=0.0),),
        now=_stamp(),
    )
    assert decision.best_candidate is None
    assert decision.confidence == 0.0


def test_run_planetary_scheduler_demo() -> None:
    decision = run_planetary_scheduler(now=_stamp())
    assert decision.best_candidate is not None
    assert len((decision.best_candidate, *decision.alternatives)) <= 5


def test_plan_top_n_validation() -> None:
    with pytest.raises(ValueError):
        plan_placements(demo_workload(), demo_sites(), top_n=0)


# --- formatter ---------------------------------------------------------------


def test_formatter_views_render() -> None:
    decision = run_planetary_scheduler(now=_stamp())
    console = Console(record=True, width=100)
    for view in ("map", "regions", "candidates", "tradeoffs", "simulation"):
        panel = PlanetarySchedulerPanel(
            workload=decision.workload,
            decision=decision,
            view=view,
        )
        console.print(panel)
    idle = PlanetarySchedulerPanel()
    console.print(idle)
    text = console.export_text()
    assert "PLANETARY SCHEDULER" in text
    assert "Simulation Only" in text


def test_formatter_empty_decision() -> None:
    wl = demo_workload()
    empty = ScheduleDecision(
        workload=wl,
        best_candidate=None,
        alternatives=(),
        confidence=0.0,
        reasoning="none",
    )
    console = Console(record=True, width=80)
    for view in ("map", "regions", "candidates", "tradeoffs", "simulation"):
        console.print(PlanetarySchedulerPanel(workload=wl, decision=empty, view=view))
    assert "PLANETARY SCHEDULER" in console.export_text()
