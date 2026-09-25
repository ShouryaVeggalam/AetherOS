"""ContextEngine — immutable operational context snapshots.

No mutable globals. Each engine instance holds the last snapshot locally;
``refresh`` rebuilds from caller-supplied inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from aetheros.bridge.adapter import GraphBridge
from aetheros.context.builder import build_context
from aetheros.context.models import GraphContext
from aetheros.graph.models import ResourceGraph
from aetheros.observatory.models import TelemetryPoint
from aetheros.policy_engine.models import TelemetrySnapshot


@dataclass
class ContextEngine:
    """Read-only context intelligence engine.

    Attributes:
        _last: Most recently built GraphContext (instance-local, not global).
    """

    _last: GraphContext | None = field(default=None, init=False, repr=False)

    def current(self) -> GraphContext | None:
        """Return the last built context, or None before the first refresh."""

        return self._last

    def refresh(
        self,
        telemetry: TelemetrySnapshot,
        *,
        resource_graph: ResourceGraph | None = None,
        bridge: GraphBridge | None = None,
        history: tuple[TelemetryPoint, ...] = (),
        manual_intent: str | None = None,
        intent_duration_seconds: float = 0.0,
        now: datetime | None = None,
    ) -> GraphContext:
        """Rebuild and store a fresh GraphContext from supplied inputs."""

        ctx = build_context(
            telemetry=telemetry,
            resource_graph=resource_graph,
            bridge=bridge,
            history=history,
            manual_intent=manual_intent,
            intent_duration_seconds=intent_duration_seconds,
            now=now,
        )
        self._last = ctx
        return ctx

    def snapshot(self) -> GraphContext | None:
        """Alias for ``current`` — returns the immutable last context."""

        return self._last
