"""Unit tests for CognitionEngine — decompose, allocate, confidence."""

from __future__ import annotations

import dataclasses

import pytest

from services.intelligence.cognition.allocate import allocate_resources
from services.intelligence.cognition.complexity import estimate_complexity
from services.intelligence.cognition.decompose import decompose_goal
from services.intelligence.cognition.service import CognitionEngine
from services.intelligence.repositories.cognition import InMemoryCognitionPlanRepository
from services.intelligence.runtime import reset_intelligence_runtime


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_intelligence_runtime()
    yield
    reset_intelligence_runtime()


@pytest.mark.asyncio
async def test_understand_basic_plan() -> None:
    engine = CognitionEngine()
    plan = await engine.understand(
        "Research latency and then implement a fix",
        {"domain": "telemetry"},
        ["Stay under 100ms SLA"],
        workspace_id="ws-1",
        created_by="operator",
    )
    assert plan.workspace_id == "ws-1"
    assert plan.status == "planned"
    assert plan.goal.startswith("Research")
    assert len(plan.objectives) >= 2
    assert plan.complexity.tier in {"trivial", "moderate", "complex", "strategic"}
    assert 0.05 <= plan.confidence <= 0.99
    assert plan.execution_steps
    assert "researcher" in plan.allocation.required_agents
    assert "executor" in plan.allocation.required_agents
    assert any("constraint" in o.statement.lower() for o in plan.objectives)


@pytest.mark.asyncio
async def test_empty_goal_rejected() -> None:
    engine = CognitionEngine()
    with pytest.raises(ValueError, match="non-empty"):
        await engine.understand("   ")


def test_decompose_splits_conjunctions() -> None:
    nodes = decompose_goal("Plan roadmap and build prototype")
    statements = [n.statement.lower() for n in nodes]
    assert any("plan roadmap" in s for s in statements)
    assert any("build prototype" in s for s in statements)


def test_allocate_never_guesses_without_evidence() -> None:
    allocation = allocate_resources("Do the thing")
    assert allocation.required_agents == ()
    assert allocation.required_knowledge == ()
    assert allocation.reasoning_budget >= 0.1


def test_allocate_uses_context_lists_as_evidence() -> None:
    allocation = allocate_resources(
        "Ship feature",
        context={"required_agents": ["executor"], "knowledge": ["policy_constraints"]},
    )
    assert "executor" in allocation.required_agents
    assert "policy_constraints" in allocation.required_knowledge


def test_complexity_tiers() -> None:
    from services.intelligence.models.types import ObjectiveNode

    shallow = (
        ObjectiveNode(id="a", statement="x", parent_id=None, depth=0, priority=1),
    )
    trivial = estimate_complexity(
        shallow,
        constraint_count=0,
        context_keys=0,
        agent_count=0,
        knowledge_count=0,
    )
    assert trivial.tier == "trivial"

    deep = tuple(
        ObjectiveNode(
            id=str(i), statement=f"s{i}", parent_id="0", depth=min(i, 3), priority=i
        )
        for i in range(10)
    )
    strategic = estimate_complexity(
        deep,
        constraint_count=5,
        context_keys=8,
        agent_count=4,
        knowledge_count=4,
    )
    assert strategic.score >= 0.45
    assert strategic.tier in {"complex", "strategic"}


@pytest.mark.asyncio
async def test_health_and_list() -> None:
    repo = InMemoryCognitionPlanRepository()
    engine = CognitionEngine(plans=repo)
    await engine.understand("Investigate CPU load", workspace_id="alpha")
    await engine.understand("Review policy compliance", workspace_id="alpha")
    health = await engine.health(workspace_id="alpha")
    assert health.plan_count == 2
    assert health.avg_confidence > 0
    assert health.last_plan_at is not None
    listed = await engine.list(workspace_id="alpha")
    assert len(listed) == 2
    empty = await engine.health(workspace_id="missing")
    assert empty.plan_count == 0
    assert empty.avg_confidence == 0.0


@pytest.mark.asyncio
async def test_plan_is_frozen() -> None:
    plan = await CognitionEngine().understand("Audit decision quality")
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        plan.confidence = 0.0  # type: ignore[misc]


def test_allocate_constraint_fallback_critic() -> None:
    allocation = allocate_resources("Do the thing", constraints=["Must finish today"])
    assert allocation.required_agents == ("critic",)


def test_decompose_depth_cap_and_duplicate_part() -> None:
    # Nested sequencing should stop at max depth without exploding.
    goal = "A then B then C then D then E"
    nodes = decompose_goal(goal)
    assert max(n.depth for n in nodes) <= 3
    assert nodes[0].parent_id is None


def test_strategic_tier_boundary() -> None:
    from services.intelligence.models.types import ObjectiveNode

    deep = tuple(
        ObjectiveNode(
            id=str(i),
            statement=f"step {i}",
            parent_id="0" if i else None,
            depth=min(i, 3),
            priority=i,
        )
        for i in range(12)
    )
    estimate = estimate_complexity(
        deep,
        constraint_count=6,
        context_keys=10,
        agent_count=5,
        knowledge_count=5,
    )
    assert estimate.tier == "strategic"
