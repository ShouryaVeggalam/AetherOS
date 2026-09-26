"""Base plugin interface for the v5 Plugin SDK.

Plugins contribute intelligence through capabilities. They must never
execute shell commands, open sockets, or mutate host state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IntelligencePlugin(ABC):
    """Abstract base class for sandboxed third-party plugins.

    Prefer declaring identity in ``plugin.yaml``; class attributes are
    fallbacks when a manifest is absent.
    """

    id: str = ""
    name: str = ""
    version: str = "0.0.0"
    author: str = "unknown"
    description: str = ""

    @abstractmethod
    def register(self, api: Any) -> None:
        """Register contributions with the sandboxed ``PluginHostAPI``."""

    def on_event(self, event: Any) -> None:
        """Optional event handler (also available via EventBus.subscribe)."""

        return None
