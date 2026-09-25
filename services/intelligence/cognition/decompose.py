"""Recursive objective decomposition — no prediction, structure only."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from services.intelligence.models.common import new_id
from services.intelligence.models.types import ObjectiveNode

_MAX_DEPTH = 3
_SPLIT_PATTERN = re.compile(
    r"\s+(?:and then|then|and|also|;|,|\||→|->)\s+",
    flags=re.IGNORECASE,
)


def decompose_goal(
    goal: str,
    *,
    constraints: Sequence[str] = (),
    context: Mapping[str, Any] | None = None,
) -> tuple[ObjectiveNode, ...]:
    """Build an objective tree from a goal statement.

    Splits on conjunctions / sequencing cues up to ``_MAX_DEPTH``.
    Constraint- and context-derived subgoals are attached only when they
    add concrete evidence (non-empty normalized text).
    """

    cleaned = " ".join(goal.split()).strip()
    if not cleaned:
        raise ValueError("goal must be a non-empty objective statement")

    root_id = new_id()
    nodes: list[ObjectiveNode] = [
        ObjectiveNode(
            id=root_id,
            statement=cleaned,
            parent_id=None,
            depth=0,
            priority=1,
        )
    ]
    _expand(cleaned, parent_id=root_id, depth=1, nodes=nodes, priority_base=10)

    for index, constraint in enumerate(constraints):
        text = " ".join(str(constraint).split()).strip()
        if not text:
            continue
        nodes.append(
            ObjectiveNode(
                id=new_id(),
                statement=f"Satisfy constraint: {text}",
                parent_id=root_id,
                depth=1,
                priority=100 + index,
            )
        )

    ctx = context or {}
    domain = ctx.get("domain")
    if isinstance(domain, str) and domain.strip():
        nodes.append(
            ObjectiveNode(
                id=new_id(),
                statement=f"Align with domain: {domain.strip()}",
                parent_id=root_id,
                depth=1,
                priority=50,
            )
        )

    return tuple(nodes)


def _expand(
    statement: str,
    *,
    parent_id: str,
    depth: int,
    nodes: list[ObjectiveNode],
    priority_base: int,
) -> None:
    if depth > _MAX_DEPTH:
        return
    parts = [p.strip() for p in _SPLIT_PATTERN.split(statement) if p.strip()]
    if len(parts) <= 1:
        return
    for offset, part in enumerate(parts):
        if part.lower() == statement.lower():
            continue
        child_id = new_id()
        nodes.append(
            ObjectiveNode(
                id=child_id,
                statement=part,
                parent_id=parent_id,
                depth=depth,
                priority=priority_base + offset,
            )
        )
        _expand(
            part,
            parent_id=child_id,
            depth=depth + 1,
            nodes=nodes,
            priority_base=priority_base * 10 + offset,
        )
