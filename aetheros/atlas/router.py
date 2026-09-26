"""Atlas router — modular keyboard → page dispatch.

Maps O/F/T/S/G/D/R/H to view renderers. Q is handled by the app loop.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

from rich.console import RenderableType

from aetheros.atlas.layout import compose_frame
from aetheros.atlas.snapshot import AtlasSnapshot
from aetheros.atlas.views import (
    render_consensus,
    render_federation,
    render_health,
    render_overview,
    render_research,
    render_scheduler,
    render_topology,
    render_twin,
)

PageId = Literal[
    "overview",
    "federation",
    "topology",
    "scheduler",
    "consensus",
    "twin",
    "research",
    "health",
]

PAGE_IDS: tuple[PageId, ...] = (
    "overview",
    "federation",
    "topology",
    "scheduler",
    "consensus",
    "twin",
    "research",
    "health",
)

HOTKEYS: Mapping[str, PageId] = {
    "o": "overview",
    "f": "federation",
    "t": "topology",
    "s": "scheduler",
    "g": "consensus",
    "d": "twin",
    "r": "research",
    "h": "health",
}

PAGE_TITLES: Mapping[PageId, str] = {
    "overview": "Overview",
    "federation": "Federation",
    "topology": "Topology",
    "scheduler": "Scheduler",
    "consensus": "Global Consensus",
    "twin": "Digital Twin",
    "research": "Research",
    "health": "Health",
}

ViewFn = Callable[[AtlasSnapshot], RenderableType]


@dataclass(frozen=True, slots=True)
class AtlasRouter:
    """Immutable registry of page renderers keyed by ``PageId``."""

    views: Mapping[PageId, ViewFn]

    @staticmethod
    def default() -> AtlasRouter:
        return AtlasRouter(
            views={
                "overview": render_overview,
                "federation": render_federation,
                "topology": render_topology,
                "scheduler": render_scheduler,
                "consensus": render_consensus,
                "twin": render_twin,
                "research": render_research,
                "health": render_health,
            }
        )

    def resolve_key(self, key: str) -> PageId | None:
        """Return target page for a hotkey, or None if not a page key."""

        if not key:
            return None
        return HOTKEYS.get(key.lower())

    def render(
        self,
        page: PageId,
        snapshot: AtlasSnapshot,
        *,
        with_chrome: bool = True,
    ) -> RenderableType:
        """Render a page (optionally wrapped in Atlas chrome)."""

        if page not in self.views:
            raise KeyError(f"unknown atlas page: {page}")
        body = self.views[page](snapshot)
        if not with_chrome:
            return body
        return compose_frame(body, page=PAGE_TITLES[page])


def normalize_page(value: str) -> PageId:
    """Normalize a page name string to a ``PageId``."""

    lowered = value.strip().lower()
    aliases = {
        "global consensus": "consensus",
        "global_consensus": "consensus",
        "digital twin": "twin",
        "digital_twin": "twin",
    }
    lowered = aliases.get(lowered, lowered)
    if lowered not in PAGE_IDS:
        raise ValueError(f"unknown page: {value}")
    return lowered  # type: ignore[return-value]
