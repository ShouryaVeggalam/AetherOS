"""Tests for Aether Lab Module 1 — Attention Engine."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from aetheros.api import create_app
from labs.aether.attention import (
    AttentionEngine,
    allocate_attention,
    derive_signals,
    signals_from_mapping,
)
from labs.aether.attention.signals import derive_signals as derive_signals_direct
from labs.aether.migrations import DOWNGRADE_SQL, REVISION, UPGRADE_SQL
from labs.aether.models import (
    AttentionAllocation,
    AttentionSignals,
    CognitionPlan,
    CognitionStage,
    Critique,
    CritiqueScore,
    Goal,
    Reflection,
    Task,
)
from labs.aether.observatory import (
    build_attention_map,
    build_replay,
    render_attention_ascii,
)
from labs.aether.repositories import AttentionRepository, PlanRepository
from labs.aether.runtime import AetherRuntime, reset_aether_runtime


def _stamp() -> datetime:
    return datetime(2026, 9, 25, 19, 0, tzinfo=UTC)


def _goal(**kwargs: object) -> Goal:
    base = {
        "id": "goal_test",
        "objective": "Design a hierarchical research architecture",
        "constraints": ("explainable", "deterministic"),
        "priority": 80.0,
        "context": {"evidence": "prior patterns", "memory_relevance": 0.7},
        "created_at": _stamp(),
    }
    base.update(kwargs)
    return Goal(**base)  # type: ignore[arg-type]


# --- models ------------------------------------------------------------------


def test_goal_validation() -> None:
    with pytest.raises(ValueError):
        Goal(id=" ", objective="o", constraints=(), priority=10, context={})
    with pytest.raises(ValueError):
        Goal(id="g", objective=" ", constraints=(), priority=10, context={})
    with pytest.raises(ValueError):
        Goal(id="g", objective="o", constraints=(), priority=101, context={})


def test_attention_signals_validation() -> None:
    with pytest.raises(ValueError):
        AttentionSignals(
            task_complexity=1.1,
            available_context=0.5,
            memory_relevance=0.5,
            uncertainty=0.5,
        )


def test_task_reflection_critique_models() -> None:
    task = Task(
        id="t1",
        parent_task=None,
        type="strategic",
        dependencies=(),
        status="pending",
        statement="Root",
    )
    assert task.depth == 0
    reflection = Reflection(
        reasoning_summary="Summary",
        weaknesses=("gap",),
        assumptions=("a1",),
        improvements=("i1",),
    )
    assert reflection.weaknesses == ("gap",)
    critique = Critique(
        id="c1",
        plan_id="p1",
        scores=(
            CritiqueScore(criterion="correctness", score=0.8),
            CritiqueScore(criterion="completeness", score=0.7),
        ),
        overall=0.75,
        verdict="revise",
    )
    assert critique.verdict == "revise"
    with pytest.raises(ValueError):
        Reflection(
            reasoning_summary=" ",
            weaknesses=(),
            assumptions=(),
            improvements=(),
        )


def test_cognition_plan_validation() -> None:
    with pytest.raises(ValueError):
        CognitionPlan(
            id=" ",
            goal_id="g",
            complexity="trivial",
            attention_budget=0.5,
            stages=(),
            confidence=0.5,
        )
    plan = CognitionPlan(
        id="p1",
        goal_id="g1",
        complexity="complex",
        attention_budget=0.6,
        stages=(
            CognitionStage(name="attention", description="alloc", attention_share=0.3),
        ),
        confidence=0.7,
    )
    assert plan.complexity == "complex"


# --- signals / allocator -----------------------------------------------------


def test_derive_signals_from_goal_evidence() -> None:
    signals = derive_signals(_goal())
    assert 0.0 <= signals.task_complexity <= 1.0
    assert signals.memory_relevance >= 0.5  # explicit context + cues
    empty = derive_signals(
        Goal(
            id="g2",
            objective="do thing",
            constraints=(),
            priority=10,
            context={},
        )
    )
    assert empty.available_context < signals.available_context


def test_derive_signals_overrides() -> None:
    signals = derive_signals(
        _goal(),
        task_complexity=0.9,
        available_context=0.1,
        memory_relevance=0.2,
        uncertainty=0.95,
    )
    assert signals.task_complexity == 0.9
    assert signals.uncertainty == 0.95


def test_signals_from_mapping() -> None:
    signals = signals_from_mapping(
        {
            "task_complexity": 0.4,
            "available_context": 0.6,
            "memory_relevance": 0.5,
            "uncertainty": 0.3,
        }
    )
    assert signals.available_context == 0.6


def test_allocate_attention_deterministic() -> None:
    signals = AttentionSignals(
        task_complexity=0.8,
        available_context=0.3,
        memory_relevance=0.7,
        uncertainty=0.6,
    )
    a = allocate_attention(signals, goal_id="g1", now=_stamp(), allocation_id="attn_fixed")
    b = allocate_attention(signals, goal_id="g1", now=_stamp(), allocation_id="attn_fixed")
    assert a.weights == b.weights
    assert a.reasoning_budget == b.reasoning_budget
    assert abs(sum(a.weights.values()) - 1.0) < 1e-6
    assert a.factors
    assert "scarce_context→boost_retrieval" in a.factors
    assert "high_complexity→boost_reasoning" in a.factors


def test_allocate_high_uncertainty_boosts_verification() -> None:
    low = allocate_attention(
        AttentionSignals(0.4, 0.7, 0.4, 0.1),
        goal_id="g",
        now=_stamp(),
    )
    high = allocate_attention(
        AttentionSignals(0.4, 0.7, 0.4, 0.9),
        goal_id="g",
        now=_stamp(),
    )
    assert high.weights["verification"] > low.weights["verification"]
    assert "high_uncertainty→boost_verification" in high.factors


# --- engine / repositories ---------------------------------------------------


@pytest.mark.asyncio
async def test_attention_engine_allocate_and_plan() -> None:
    engine = AttentionEngine()
    goal, allocation = await engine.allocate_from_objective(
        "Complex multi-step strategic system architecture under uncertain evidence",
        constraints=["no live mutation"],
        priority=90,
        context={"memory": "prior"},
        now=_stamp(),
        goal_id="goal_engine",
    )
    assert goal.id == "goal_engine"
    assert allocation.goal_id == goal.id
    plan = await engine.draft_plan(goal, allocation, now=_stamp())
    assert plan.attention_id == allocation.id
    assert plan.stages
    assert await engine.get_allocation(allocation.id) is allocation
    assert await engine.get_plan(plan.id) is plan


@pytest.mark.asyncio
async def test_repositories_append_only() -> None:
    repo = AttentionRepository()
    signals = AttentionSignals(0.5, 0.5, 0.5, 0.5)
    alloc = allocate_attention(signals, goal_id="g", now=_stamp(), allocation_id="a1")
    await repo.append(alloc)
    with pytest.raises(ValueError):
        await repo.append(alloc)
    listed = await repo.list_for_goal("g")
    assert len(listed) == 1
    assert len(await repo.list_all()) == 1

    plans = PlanRepository()
    plan = CognitionPlan(
        id="p1",
        goal_id="g",
        complexity="moderate",
        attention_budget=0.4,
        stages=(),
        confidence=0.5,
        created_at=_stamp(),
    )
    await plans.append(plan)
    with pytest.raises(ValueError):
        await plans.append(plan)
    assert await plans.get("p1") is plan
    assert len(await plans.list_for_goal("g")) == 1
    assert len(await plans.list_all()) == 1


@pytest.mark.asyncio
async def test_runtime_health() -> None:
    rt = reset_aether_runtime(AetherRuntime())
    health = await rt.health()
    assert health.status == "ok"
    assert "attention" in health.modules_ready
    await rt.attention.allocate_from_objective("study patterns", now=_stamp())
    health2 = await rt.health()
    assert health2.attention_count == 1


# --- observatory -------------------------------------------------------------


def test_observatory_heatmap_and_replay() -> None:
    signals = AttentionSignals(0.7, 0.4, 0.6, 0.5)
    alloc = allocate_attention(signals, goal_id="g", now=_stamp(), allocation_id="attn_map")
    view = build_attention_map(alloc)
    assert len(view.cells) == 4
    ascii_map = render_attention_ascii(view)
    assert "ATTENTION MAP" in ascii_map
    assert "focus" in ascii_map
    plan = CognitionPlan(
        id="p",
        goal_id="g",
        complexity="complex",
        attention_budget=0.5,
        stages=(
            CognitionStage(name="attention", description="a", attention_share=0.3),
            CognitionStage(name="critique", description="c", attention_share=0.2),
        ),
        confidence=0.6,
    )
    frames = build_replay(plan)
    assert [f.stage for f in frames] == ["attention", "critique"]


# --- migrations --------------------------------------------------------------


def test_migration_sql_present() -> None:
    assert REVISION.startswith("0001")
    assert "aether_attention_allocations" in UPGRADE_SQL
    assert "DROP TABLE" in DOWNGRADE_SQL


# --- API ---------------------------------------------------------------------


@pytest.fixture()
def client() -> TestClient:
    reset_aether_runtime(AetherRuntime())
    return TestClient(create_app())


def test_api_attention_allocate(client: TestClient) -> None:
    res = client.post(
        "/aether/attention",
        json={
            "objective": "Investigate uncertain hierarchical architecture",
            "priority": 70,
            "constraints": ["deterministic"],
            "context": {"memory_relevance": 0.55},
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["goal_id"]
    assert abs(sum(body["weights"].values()) - 1.0) < 1e-5
    get = client.get(f"/aether/attention/{body['id']}")
    assert get.status_code == 200
    assert client.get("/aether/attention/missing").status_code == 404


def test_api_cognition_and_plans(client: TestClient) -> None:
    res = client.post(
        "/aether/cognition",
        json={
            "objective": "Complex strategic multi-step system under risk",
            "priority": 85,
            "constraints": ["explainable"],
            "signals": {
                "task_complexity": 0.85,
                "available_context": 0.4,
                "memory_relevance": 0.5,
                "uncertainty": 0.7,
            },
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["plan"]["attention_id"] == body["attention"]["id"]
    plan_id = body["plan"]["id"]
    fetched = client.get(f"/aether/plans/{plan_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == plan_id
    assert client.get("/aether/plans/nope").status_code == 404


def test_api_pending_modules_and_health(client: TestClient) -> None:
    assert client.get("/aether/health").json()["status"] == "ok"
    assert client.post(
        "/aether/decompose",
        json={"objective": "break this down"},
    ).json()["status"] == "pending"
    assert client.post(
        "/aether/reflect",
        json={"plan_id": "p", "reasoning_summary": "summary text"},
    ).json()["module"] == "reflection"
    assert client.post(
        "/aether/critique",
        json={"plan_id": "p", "reasoning_summary": "summary text"},
    ).json()["module"] == "critique"


def test_api_attention_validation_error(client: TestClient) -> None:
    res = client.post(
        "/aether/attention",
        json={"objective": "x", "priority": 50, "signals": {"task_complexity": 2.0}},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_async_client_cognition() -> None:
    reset_aether_runtime(AetherRuntime())
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            "/aether/cognition",
            json={"objective": "allocate attention for research"},
        )
        assert res.status_code == 200


def test_allocation_weight_sum_enforced() -> None:
    signals = AttentionSignals(0.5, 0.5, 0.5, 0.5)
    with pytest.raises(ValueError):
        AttentionAllocation(
            id="bad",
            goal_id="g",
            signals=signals,
            weights={
                "focus": 0.5,
                "memory": 0.5,
                "exploration": 0.5,
                "verification": 0.5,
            },
            reasoning_budget=0.5,
            retrieval_budget=0.5,
            factors=(),
            confidence=0.5,
            created_at=_stamp(),
        )


def test_uncertain_sparse_goal_signals() -> None:
    signals = derive_signals_direct(
        Goal(
            id="g",
            objective="maybe unclear unknown risk",
            constraints=(),
            priority=80,
            context={},
        )
    )
    assert signals.uncertainty >= 0.4


def test_coverage_edges() -> None:
    # Model validation branches
    with pytest.raises(ValueError):
        AttentionAllocation(
            id=" ",
            goal_id="g",
            signals=AttentionSignals(0.5, 0.5, 0.5, 0.5),
            weights={
                "focus": 0.25,
                "memory": 0.25,
                "exploration": 0.25,
                "verification": 0.25,
            },
            reasoning_budget=0.5,
            retrieval_budget=0.5,
            factors=(),
            confidence=0.5,
            created_at=_stamp(),
        )
    with pytest.raises(ValueError):
        AttentionAllocation(
            id="a",
            goal_id=" ",
            signals=AttentionSignals(0.5, 0.5, 0.5, 0.5),
            weights={
                "focus": 0.25,
                "memory": 0.25,
                "exploration": 0.25,
                "verification": 0.25,
            },
            reasoning_budget=0.5,
            retrieval_budget=0.5,
            factors=(),
            confidence=0.5,
            created_at=_stamp(),
        )
    with pytest.raises(ValueError):
        AttentionAllocation(
            id="a",
            goal_id="g",
            signals=AttentionSignals(0.5, 0.5, 0.5, 0.5),
            weights={
                "focus": 0.25,
                "memory": 0.25,
                "exploration": 0.25,
                "verification": 0.25,
            },
            reasoning_budget=1.5,
            retrieval_budget=0.5,
            factors=(),
            confidence=0.5,
            created_at=_stamp(),
        )
    with pytest.raises(ValueError):
        AttentionAllocation(
            id="a",
            goal_id="g",
            signals=AttentionSignals(0.5, 0.5, 0.5, 0.5),
            weights={
                "focus": 0.25,
                "memory": 0.25,
                "exploration": 0.25,
                "verification": 0.25,
            },
            reasoning_budget=0.5,
            retrieval_budget=-0.1,
            factors=(),
            confidence=0.5,
            created_at=_stamp(),
        )
    with pytest.raises(ValueError):
        AttentionAllocation(
            id="a",
            goal_id="g",
            signals=AttentionSignals(0.5, 0.5, 0.5, 0.5),
            weights={
                "focus": 0.25,
                "memory": 0.25,
                "exploration": 0.25,
                "verification": 0.25,
            },
            reasoning_budget=0.5,
            retrieval_budget=0.5,
            factors=(),
            confidence=1.5,
            created_at=_stamp(),
        )
    with pytest.raises(ValueError):
        CognitionStage(name=" ", description="d", attention_share=0.1)
    with pytest.raises(ValueError):
        CognitionStage(name="n", description="d", attention_share=1.5)
    with pytest.raises(ValueError):
        CognitionPlan(
            id="p",
            goal_id=" ",
            complexity="trivial",
            attention_budget=0.5,
            stages=(),
            confidence=0.5,
        )
    with pytest.raises(ValueError):
        CognitionPlan(
            id="p",
            goal_id="g",
            complexity="trivial",
            attention_budget=1.5,
            stages=(),
            confidence=0.5,
        )
    with pytest.raises(ValueError):
        CognitionPlan(
            id="p",
            goal_id="g",
            complexity="trivial",
            attention_budget=0.5,
            stages=(),
            confidence=1.5,
        )
    with pytest.raises(ValueError):
        Task(
            id=" ",
            parent_task=None,
            type="strategic",
            dependencies=(),
            status="pending",
        )
    with pytest.raises(ValueError):
        Task(
            id="t",
            parent_task=None,
            type="strategic",
            dependencies=(),
            status="pending",
            depth=-1,
        )
    with pytest.raises(ValueError):
        CritiqueScore(criterion="correctness", score=1.5)
    with pytest.raises(ValueError):
        Critique(
            id=" ",
            plan_id="p",
            scores=(),
            overall=0.5,
            verdict="pass",
        )
    with pytest.raises(ValueError):
        Critique(
            id="c",
            plan_id="p",
            scores=(),
            overall=1.2,
            verdict="pass",
        )

    # Sequence context + empty nested values in signal derivation
    signals = derive_signals(
        Goal(
            id="g",
            objective="plan with known evidence precedent",
            constraints=("policy",),
            priority=40,
            context={
                "tags": ["a", "b"],
                "empty": "",
                "none": None,
                "blank_list": [],
                "evidence_score": 80,
            },
        )
    )
    assert signals.memory_relevance > 0.3

    # Allocator equal-weight fallback path
    from labs.aether.attention import allocator as alloc_mod

    equal = alloc_mod._normalize(
        {"focus": 0.0, "memory": 0.0, "exploration": 0.0, "verification": 0.0}
    )
    assert equal["focus"] == 0.25

    # Engine property accessors
    engine = AttentionEngine()
    assert engine.attention_repo is not None
    assert engine.plan_repo is not None


@pytest.mark.asyncio
async def test_engine_missing_lookups() -> None:
    engine = AttentionEngine()
    assert await engine.get_allocation("missing") is None
    assert await engine.get_plan("missing") is None


@pytest.mark.asyncio
async def test_draft_plan_complexity_tiers() -> None:
    engine = AttentionEngine()
    for complexity, expected in (
        (0.1, "trivial"),
        (0.3, "moderate"),
        (0.6, "complex"),
        (0.9, "strategic"),
    ):
        goal, allocation = await engine.allocate_from_objective(
            f"tier check {complexity}",
            now=_stamp(),
            task_complexity=complexity,
            available_context=0.5,
            memory_relevance=0.5,
            uncertainty=0.2,
        )
        plan = await engine.draft_plan(goal, allocation, now=_stamp())
        assert plan.complexity == expected


def test_api_value_error_paths(client: TestClient) -> None:
    # Empty objective after strip triggers Goal validation via engine
    res = client.post("/aether/attention", json={"objective": "   "})
    assert res.status_code == 422
    res2 = client.post("/aether/cognition", json={"objective": "   "})
    assert res2.status_code == 422


def test_get_aether_runtime_singleton() -> None:
    from labs.aether.runtime import get_aether_runtime

    reset_aether_runtime(None)
    a = get_aether_runtime()
    b = get_aether_runtime()
    assert a is b
