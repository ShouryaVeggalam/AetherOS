"""Sandboxed host API handed to plugins at ``register()`` time.

Aggregates capability checks, event bus, and read-only graph/context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from plugins.sdk.capabilities import CapabilityRegistry
from plugins.sdk.context import ContextAPI, GraphAPI
from plugins.sdk.events import EventBus, EventHandler


@dataclass
class PluginHostAPI:
    """Safe API surface for IntelligencePlugin.register().

    Write paths are limited to capability registration and event
    subscription. Graph / context remain read-only snapshots.
    """

    capabilities: CapabilityRegistry = field(default_factory=CapabilityRegistry)
    events: EventBus = field(default_factory=EventBus)
    graph: GraphAPI = field(default_factory=GraphAPI)
    context: ContextAPI = field(default_factory=ContextAPI)
    _notes: list[str] = field(default_factory=list)
    _metadata: dict[str, Any] = field(default_factory=dict)

    def require(self, capability: str) -> None:
        """Raise if ``capability`` was not granted for this session."""

        self.capabilities.require(capability)

    def subscribe(self, topic: str, handler: EventHandler) -> None:
        """Subscribe to a topic (requires ``events.subscribe``)."""

        self.capabilities.require("events.subscribe")
        self.events.subscribe(topic, handler)

    def read_graph(self) -> GraphAPI:
        """Return the read-only graph facade (requires ``graph.read``)."""

        self.capabilities.require("graph.read")
        return self.graph

    def read_context(self) -> ContextAPI:
        """Return the read-only context facade (requires ``context.read``)."""

        self.capabilities.require("context.read")
        return self.context

    def contribute_note(self, text: str) -> None:
        """Record an advisory note (never executed as an action)."""

        cleaned = text.strip()
        if cleaned:
            self._notes.append(cleaned)

    def notes(self) -> tuple[str, ...]:
        return tuple(self._notes)

    def set_meta(self, key: str, value: Any) -> None:
        """Store non-sensitive plugin session metadata."""

        self._metadata[str(key)] = value

    def meta(self) -> dict[str, Any]:
        return dict(self._metadata)

    def stamp(self) -> str:
        """UTC timestamp string for plugin logging (text only)."""

        return datetime.now(UTC).isoformat()
