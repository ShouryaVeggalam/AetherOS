"""Global Knowledge Graph relationship catalog.

Only verified edge kinds. Never invent speculative links in the builder.
"""

from __future__ import annotations

from typing import Literal

GlobalRelation = Literal[
    "HOSTS",
    "CONTAINS",
    "DEPENDS_ON",
    "COMMUNICATES",
    "CAUSES",
    "CORRELATES",
    "SIMULATES",
    "VERIFIED_BY",
    "REPLICATES",
    "PREDICTS",
]

GLOBAL_RELATIONS: frozenset[str] = frozenset(
    {
        "HOSTS",
        "CONTAINS",
        "DEPENDS_ON",
        "COMMUNICATES",
        "CAUSES",
        "CORRELATES",
        "SIMULATES",
        "VERIFIED_BY",
        "REPLICATES",
        "PREDICTS",
    }
)


def is_global_relation(value: str) -> bool:
    """True when ``value`` is a supported Global Knowledge Graph relation."""

    return value in GLOBAL_RELATIONS
