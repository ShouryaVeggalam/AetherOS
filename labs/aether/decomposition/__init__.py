"""Decomposition Engine — Module 2."""

from __future__ import annotations

from labs.aether.decomposition.engine import (
    decompose_objective,
    topological_order,
    validate_dag,
)
from labs.aether.decomposition.service import DecompositionEngine

__all__ = [
    "DecompositionEngine",
    "decompose_objective",
    "topological_order",
    "validate_dag",
]
