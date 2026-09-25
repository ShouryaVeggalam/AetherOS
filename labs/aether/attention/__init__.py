"""Module 1 — Attention Engine.

Adaptive, deterministic allocation of cognitive attention budgets.
"""

from __future__ import annotations

from labs.aether.attention.allocator import allocate_attention
from labs.aether.attention.service import AttentionEngine
from labs.aether.attention.signals import derive_signals, signals_from_mapping

__all__ = [
    "AttentionEngine",
    "allocate_attention",
    "derive_signals",
    "signals_from_mapping",
]
