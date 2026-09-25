"""Repository tests — append-only and immutability."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from services.intelligence.models.types import (
    CognitionPlan,
    ComplexityEstimate,
    ObjectiveNode,
    ResourceAllocation,
)
from services.intelligence.repositories.cognition import InMemoryCognitionPlanRepository


def _plan(plan_id: str, workspace_id: str = "ws") -> CognitionPlan:
    return CognitionPlan(
        id=plan_id,
        workspace_id=workspace_id,
        goal="Test goal",
        context={},
        constraints=(),
        objectives=(
            ObjectiveNode(
                id="obj-1",
                statement="Test goal",
                parent_id=None,
                depth=0,
                priority=1,
            ),
        ),
        complexity=ComplexityEstimate(score=0.1, tier="trivial", factors=("single_objective",)),
        allocation=ResourceAllocation(
            required_agents=(),
            required_knowledge=(),
            reasoning_budget=0.15,
        ),
        execution_steps=("Validate objective and constraints",),
        confidence=0.7,
        created_by="tester",
        created_at=datetime.now(UTC),
        status="planned",
    )


@pytest.mark.asyncio
async def test_append_get_list() -> None:
    repo = InMemoryCognitionPlanRepository()
    a = await repo.append(_plan("a", "w1"))
    b = await repo.append(_plan("b", "w1"))
    await repo.append(_plan("c", "w2"))
    assert await repo.get("a") is a
    assert await repo.get("missing") is None
    listed = await repo.list(workspace_id="w1")
    assert {p.id for p in listed} == {"a", "b"}
    assert len(repo) == 3
    assert b.goal == "Test goal"


@pytest.mark.asyncio
async def test_duplicate_id_rejected() -> None:
    repo = InMemoryCognitionPlanRepository()
    await repo.append(_plan("dup"))
    with pytest.raises(ValueError, match="already exists"):
        await repo.append(_plan("dup"))


@pytest.mark.asyncio
async def test_stored_plan_immutable() -> None:
    repo = InMemoryCognitionPlanRepository()
    plan = await repo.append(_plan("frozen"))
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        plan.goal = "mutated"  # type: ignore[misc]
