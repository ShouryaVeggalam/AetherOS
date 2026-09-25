"""Tests for Aether Lab Modules 2–4: decompose, plan, reflect, critique."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from labs.aether.cognition import CognitionEngine
from labs.aether.critique import CritiqueEngine, critique_reasoning
from labs.aether.decomposition import (
    DecompositionEngine,
    decompose_objective,
    topological_order,
    validate_dag,
)
from labs.aether.models import Goal, Task, TaskGraph
from labs.aether.observatory import (
    build_reflection_timeline,
    build_task_graph_view,
    render_critique_ascii,
    render_task_graph_ascii,
)
from labs.aether.planning import PlanningEngine, build_plan_from_graph, revise_plan
from labs.aether.reflection import ReflectionEngine, reflect_on_reasoning
from labs.aether.runtime import AetherRuntime, reset_aether_runtime


def _stamp() -> datetime:
    return datetime(2026, 9, 25, 20, 0, tzinfo=UTC)


def _goal(**kwargs: object) -> Goal:
    base: dict[str, object] = {
        "id": "goal_m2",
        "objective": "Design hierarchical research architecture under uncertainty",
        "constraints": ("explainable", "deterministic"),
        "priority": 80.0,
        "context": {"evidence": "prior"},
        "created_at": _stamp(),
    }
    base.update(kwargs)
    return Goal(**base)  # type: ignore[arg-type]


def test_decompose_builds_dag_levels() -> None:
    graph = decompose_objective(_goal(), max_depth=4, now=_stamp(), graph_id="tg_fixed")
    types = {t.type for t in graph.tasks}
    assert "strategic" in types
    assert "tactical" in types
    assert "operational" in types
    assert "execution" in types
    factors = validate_dag(graph)
    assert any(f.startswith("tasks=") for f in factors)
    order = topological_order(graph)
    assert len(order) == len(graph.tasks)
    assert order[0].type == "strategic"


def test_decompose_max_depth_bounds() -> None:
    shallow = decompose_objective(_goal(), max_depth=1, now=_stamp())
    assert all(t.type == "strategic" for t in shallow.tasks)
    with pytest.raises(ValueError):
        decompose_objective(_goal(), max_depth=0)


def test_task_graph_validation() -> None:
    with pytest.raises(ValueError):
        TaskGraph(
            id=" ",
            goal_id="g",
            objective="o",
            tasks=(),
            roots=(),
            max_depth=0,
        )
    with pytest.raises(ValueError):
        TaskGraph(
            id="tg",
            goal_id="g",
            objective="o",
            tasks=(
                Task(
                    id="t1",
                    parent_task=None,
                    type="strategic",
                    dependencies=("missing",),
                    status="ready",
                ),
            ),
            roots=("t1",),
            max_depth=0,
        )


@pytest.mark.asyncio
async def test_decomposition_and_planning_engines() -> None:
    rt = reset_aether_runtime(AetherRuntime())
    goal = _goal()
    graph = await rt.decomposition.decompose(goal, max_depth=3, now=_stamp())
    assert await rt.decomposition.get(graph.id) is graph
    _, allocation = await rt.attention.allocate_from_objective(
        goal.objective,
        constraints=goal.constraints,
        priority=goal.priority,
        context=goal.context,
        goal_id=goal.id,
        now=_stamp(),
    )
    plan = await rt.planning.plan(goal, allocation, graph, now=_stamp())
    assert plan.task_graph_id == graph.id
    assert plan.status == "active"
    assert plan.stages


@pytest.mark.asyncio
async def test_cognition_pipeline_end_to_end() -> None:
    rt = reset_aether_runtime(AetherRuntime())
    bundle = await rt.cognition.run(
        "Strategic multi-step research system architecture",
        constraints=["explainable"],
        priority=85,
        max_depth=4,
        now=_stamp(),
        task_complexity=0.8,
        uncertainty=0.6,
    )
    assert bundle.task_graph.tasks
    assert bundle.plan.attention_id == bundle.attention.id
    view = build_task_graph_view(bundle.task_graph)
    ascii_g = render_task_graph_ascii(view)
    assert "TASK GRAPH" in ascii_g


@pytest.mark.asyncio
async def test_reflection_and_revise() -> None:
    rt = reset_aether_runtime(AetherRuntime())
    bundle = await rt.cognition.run(
        "Complex architecture under unknown risk",
        priority=75,
        now=_stamp(),
    )
    reflection, revised = await rt.cognition.reflect(
        bundle.plan,
        reasoning_summary=(
            "We assume the platform scales. Maybe evidence is missing "
            "and the gap is unknown."
        ),
        evidence=(),
        revise=True,
        now=_stamp(),
    )
    assert reflection.weaknesses
    assert reflection.assumptions
    assert reflection.improvements
    assert revised is not None
    assert revised.status == "revised"
    assert revised.parent_plan_id == bundle.plan.id
    timeline = build_reflection_timeline((reflection,))
    assert timeline[0].weakness_count >= 1


@pytest.mark.asyncio
async def test_critique_engine_verdicts() -> None:
    rt = reset_aether_runtime(AetherRuntime())
    bundle = await rt.cognition.run(
        "Strategic evidence-backed architecture plan",
        priority=70,
        now=_stamp(),
        task_complexity=0.7,
    )
    strong = await rt.cognition.critique(
        bundle.plan,
        reasoning_summary=(
            "Therefore the strategic plan holds because evidence supports "
            "architecture boundaries and verification checkpoints."
        ),
        evidence=("e1", "e2", "e3", "e4"),
        now=_stamp(),
    )
    assert strong.overall > 0.4
    assert len(strong.scores) == 5
    assert strong.verdict in ("pass", "revise", "reject")
    ascii_c = render_critique_ascii(strong)
    assert "CRITIQUE" in ascii_c

    weak = critique_reasoning(
        plan=bundle.plan,
        reasoning_summary="unclear",
        evidence=(),
        now=_stamp(),
        critique_id="crit_weak",
    )
    assert weak.verdict in ("revise", "reject")


def test_reflect_on_reasoning_requires_summary() -> None:
    from labs.aether.models import CognitionPlan

    plan = CognitionPlan(
        id="p",
        goal_id="g",
        complexity="moderate",
        attention_budget=0.5,
        stages=(),
        confidence=0.5,
    )
    with pytest.raises(ValueError):
        reflect_on_reasoning(plan=plan, reasoning_summary=" ")


def test_revise_plan_adds_improvement_stages() -> None:
    from labs.aether.attention import allocate_attention
    from labs.aether.models import AttentionSignals

    goal = _goal()
    graph = decompose_objective(goal, max_depth=2, now=_stamp())
    allocation = allocate_attention(
        AttentionSignals(0.5, 0.5, 0.5, 0.5),
        goal_id=goal.id,
        now=_stamp(),
        allocation_id="attn_rev",
    )
    plan = build_plan_from_graph(goal, allocation, graph, now=_stamp())
    revised = revise_plan(
        plan,
        improvements=("Add evidence", "Clarify assumptions"),
        now=_stamp(),
    )
    assert revised.status == "revised"
    assert any(s.name.startswith("improvement_") for s in revised.stages)


@pytest.mark.asyncio
async def test_engine_getters_and_repos() -> None:
    decomp = DecompositionEngine()
    assert await decomp.get("missing") is None
    planning = PlanningEngine()
    assert await planning.get("missing") is None
    reflection = ReflectionEngine()
    assert await reflection.get("missing") is None
    critique = CritiqueEngine()
    assert await critique.get("missing") is None
    assert isinstance(
        CognitionEngine(
            attention=AetherRuntime().attention,
            decomposition=decomp,
            planning=planning,
        ),
        CognitionEngine,
    )
