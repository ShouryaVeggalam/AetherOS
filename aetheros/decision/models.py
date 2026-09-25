"""Decision-engine data contracts.

Re-exports the shared ``Decision`` advice type from ``aetheros.advice``
so existing ``from aetheros.decision.models import Decision`` call sites
keep working.
"""

from __future__ import annotations

from aetheros.advice.decision import Decision, SeverityLevel, utc_now

__all__ = [
    "Decision",
    "SeverityLevel",
    "utc_now",
]
