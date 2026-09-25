"""Security Agent module alias (P4 folder layout).

Re-exports the existing SecurityAgent without changing behavior.
"""

from __future__ import annotations

from aetheros.agents.security_agent import SecurityAgent

__all__ = ["SecurityAgent"]
