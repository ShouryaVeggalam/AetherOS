"""Evidence-gated agent and knowledge allocation."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from services.intelligence.models.types import ResourceAllocation

# Capability catalog: agent → evidence keyword patterns (case-insensitive).
_AGENT_CUES: dict[str, tuple[str, ...]] = {
    "researcher": ("research", "investigate", "survey", "analyze", "study", "discover"),
    "planner": ("plan", "roadmap", "schedule", "strategy", "decompose", "milestone"),
    "critic": ("review", "audit", "critique", "verify", "validate", "evaluate"),
    "executor": ("implement", "execute", "deploy", "build", "ship", "run", "operate"),
    "coordinator": ("coordinate", "orchestrate", "multi-agent", "society", "team"),
}

_KNOWLEDGE_CUES: dict[str, tuple[str, ...]] = {
    "domain_ontology": ("ontology", "taxonomy", "schema", "entity", "knowledge graph"),
    "operational_telemetry": ("cpu", "memory", "latency", "telemetry", "metric", "load"),
    "policy_constraints": ("policy", "compliance", "constraint", "regulation", "sla"),
    "scientific_literature": ("paper", "scientific", "experiment", "theorem", "evidence"),
    "world_entities": ("market", "company", "geography", "region", "world"),
}


def allocate_resources(
    goal: str,
    *,
    context: Mapping[str, Any] | None = None,
    constraints: Sequence[str] = (),
    objective_count: int = 1,
) -> ResourceAllocation:
    """Select agents and knowledge domains only when keyword evidence exists.

    Never guesses. Empty evidence yields a minimal critic-only allocation
    when constraints exist; otherwise an empty agent set with a low budget.
    """

    corpus = _corpus(goal, context=context, constraints=constraints)
    agents = _match(_AGENT_CUES, corpus)
    knowledge = _match(_KNOWLEDGE_CUES, corpus)

    # Explicit context lists are evidence when present.
    ctx = context or {}
    for key, bucket in (
        ("required_agents", agents),
        ("agents", agents),
        ("required_knowledge", knowledge),
        ("knowledge", knowledge),
    ):
        raw = ctx.get(key)
        if isinstance(raw, (list, tuple)):
            for item in raw:
                text = str(item).strip().lower()
                if text and text not in bucket:
                    bucket.append(text)

    if not agents and constraints:
        agents.append("critic")

    reasoning_budget = _budget(
        agent_count=len(agents),
        knowledge_count=len(knowledge),
        objective_count=objective_count,
        constraint_count=len(constraints),
    )
    return ResourceAllocation(
        required_agents=tuple(agents),
        required_knowledge=tuple(knowledge),
        reasoning_budget=reasoning_budget,
    )


def _corpus(
    goal: str,
    *,
    context: Mapping[str, Any] | None,
    constraints: Sequence[str],
) -> str:
    parts = [goal]
    parts.extend(str(c) for c in constraints)
    if context:
        for key, value in context.items():
            parts.append(str(key))
            if isinstance(value, (str, int, float)):
                parts.append(str(value))
            elif isinstance(value, (list, tuple)):
                parts.extend(str(v) for v in value)
    return " ".join(parts).lower()


def _match(catalog: dict[str, tuple[str, ...]], corpus: str) -> list[str]:
    selected: list[str] = []
    for name, cues in catalog.items():
        for cue in cues:
            if re.search(rf"\b{re.escape(cue)}\b", corpus):
                selected.append(name)
                break
    return selected


def _budget(
    *,
    agent_count: int,
    knowledge_count: int,
    objective_count: int,
    constraint_count: int,
) -> float:
    raw = (
        0.15
        + 0.12 * agent_count
        + 0.08 * knowledge_count
        + 0.05 * max(0, objective_count - 1)
        + 0.04 * constraint_count
    )
    return round(max(0.1, min(1.0, raw)), 4)
