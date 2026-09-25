"""Causal Knowledge Graph relationship catalog and edge helpers.

P3 edge types are independent of ``CausalRelationKind`` (cognitive catalog)
and of Genesis ``OntologyRelationKind``. No speculative edges.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Literal

KnowledgeRelation = Literal[
    "CAUSES",
    "USES",
    "ALLOCATES",
    "DEPENDS_ON",
    "PRECEDES",
    "CORRELATES",
    "PREDICTS",
    "VERIFIED_BY",
]

KNOWLEDGE_RELATIONS: frozenset[str] = frozenset(
    {
        "CAUSES",
        "USES",
        "ALLOCATES",
        "DEPENDS_ON",
        "PRECEDES",
        "CORRELATES",
        "PREDICTS",
        "VERIFIED_BY",
    }
)

# Relations treated as causal for traversal helpers.
CAUSAL_RELATIONS: frozenset[str] = frozenset({"CAUSES", "PRECEDES", "PREDICTS"})


def is_knowledge_relation(value: str) -> bool:
    """Return True when ``value`` is a supported Knowledge Graph edge type."""

    return value in KNOWLEDGE_RELATIONS


def edge_key(source: str, target: str, relationship: str) -> tuple[str, str, str]:
    """Canonical deduplication key for a directed typed edge."""

    return (source, target, relationship)


def dedupe_edge_keys(
    keys: Iterable[tuple[str, str, str]],
) -> tuple[tuple[str, str, str], ...]:
    """Return unique edge keys preserving first-seen order."""

    seen: set[tuple[str, str, str]] = set()
    ordered: list[tuple[str, str, str]] = []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        ordered.append(key)
    return tuple(ordered)


def map_resource_relation(relation: str) -> KnowledgeRelation | None:
    """Map a Resource Graph edge relation onto a Knowledge relation when safe.

    Unsupported Resource Graph relations (COMMUNICATES, SIMULATES) yield None
    so builders never invent speculative links.
    """

    mapping: dict[str, KnowledgeRelation] = {
        "USES": "USES",
        "ALLOCATES": "ALLOCATES",
        "DEPENDS_ON": "DEPENDS_ON",
        "PREDICTS": "PREDICTS",
    }
    return mapping.get(relation)


def merge_confidence(values: Sequence[float]) -> float:
    """Deterministic confidence merge: max, capped at 99."""

    if not values:
        return 0.0
    return round(min(99.0, max(values)), 2)
