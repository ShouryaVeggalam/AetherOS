"""Cognition orchestrator — attention → decompose → plan (+ optional reflect/critique)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from labs.aether.attention.service import AttentionEngine
from labs.aether.critique.service import CritiqueEngine
from labs.aether.decomposition.service import DecompositionEngine
from labs.aether.models.types import (
    AttentionAllocation,
    CognitionPlan,
    Critique,
    Goal,
    Reflection,
    TaskGraph,
)
from labs.aether.planning.service import PlanningEngine
from labs.aether.reflection.service import ReflectionEngine


@dataclass(frozen=True, slots=True)
class CognitionBundle:
    """Full cognition pipeline result."""

    goal: Goal
    attention: AttentionAllocation
    task_graph: TaskGraph
    plan: CognitionPlan


class CognitionEngine:
    """Executive cognition pipeline for Aether Lab."""

    def __init__(
        self,
        *,
        attention: AttentionEngine,
        decomposition: DecompositionEngine,
        planning: PlanningEngine,
        reflection: ReflectionEngine | None = None,
        critique: CritiqueEngine | None = None,
    ) -> None:
        self.attention = attention
        self.decomposition = decomposition
        self.planning = planning
        self.reflection_engine = reflection or ReflectionEngine()
        self.critique_engine = critique or CritiqueEngine()

    async def run(
        self,
        objective: str,
        *,
        constraints: Sequence[str] = (),
        priority: float = 50.0,
        context: Mapping[str, Any] | None = None,
        goal_id: str | None = None,
        max_depth: int = 3,
        now: datetime | None = None,
        task_complexity: float | None = None,
        available_context: float | None = None,
        memory_relevance: float | None = None,
        uncertainty: float | None = None,
    ) -> CognitionBundle:
        stamp = now or datetime.now(UTC)
        goal, allocation = await self.attention.allocate_from_objective(
            objective,
            constraints=constraints,
            priority=priority,
            context=context,
            goal_id=goal_id or f"goal_{uuid4().hex[:12]}",
            now=stamp,
            task_complexity=task_complexity,
            available_context=available_context,
            memory_relevance=memory_relevance,
            uncertainty=uncertainty,
        )
        graph = await self.decomposition.decompose(goal, max_depth=max_depth, now=stamp)
        plan = await self.planning.plan(goal, allocation, graph, now=stamp)
        return CognitionBundle(
            goal=goal,
            attention=allocation,
            task_graph=graph,
            plan=plan,
        )

    async def reflect(
        self,
        plan: CognitionPlan,
        *,
        reasoning_summary: str,
        evidence: Sequence[str] = (),
        now: datetime | None = None,
        revise: bool = True,
    ) -> tuple[Reflection, CognitionPlan | None]:
        reflection = await self.reflection_engine.reflect(
            plan,
            reasoning_summary=reasoning_summary,
            evidence=evidence,
            now=now,
        )
        revised = None
        if revise and reflection.improvements:
            revised = await self.planning.revise(
                plan,
                improvements=reflection.improvements,
                now=now,
            )
        return reflection, revised

    async def critique(
        self,
        plan: CognitionPlan,
        *,
        reasoning_summary: str,
        evidence: Sequence[str] = (),
        reflection: Reflection | None = None,
        now: datetime | None = None,
    ) -> Critique:
        return await self.critique_engine.critique(
            plan,
            reasoning_summary=reasoning_summary,
            evidence=evidence,
            reflection=reflection,
            now=now,
        )
