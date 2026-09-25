"""Shared advice contracts — decision/intent-neutral value types.

Owns ``Decision`` so ``intent`` can weight scores without importing the
``decision`` package (avoids decision ↔ intent package cycles).
"""

from __future__ import annotations

from aetheros.advice.decision import Decision, SeverityLevel, utc_now

__all__ = [
    "Decision",
    "SeverityLevel",
    "utc_now",
]
