"""Horizon Observatory router — modular keyboard → page dispatch.

Maps O/C/T/K/W/D/G/R/H to view renderers. Q is handled by the app loop.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Literal

from rich.console import RenderableType

from aetheros.horizon.layout import compose_frame
from aetheros.horizon.snapshot import HorizonSnapshot
from aetheros.horizon.views import (
    render_cloud,
    render_consensus,
    render_health,
    render_knowledge,
    render_overview,
    render_research,
    render_scheduler,
    render_topology,
    render_twin,
)

PageId = Literal[
    "overview",
    "cloud",
    "topology",
    "knowledge",
    "scheduler",
    "twin",
    "consensus",
    "research",
    "health",
]

PAGE_IDS: tuple[PageId, ...] = (
    "overview",
    "cloud",
    "topology",
    "knowledge",
    "scheduler",
    "twin",
    "consensus",
    "research",
    "health",
)

HOTKEYS: Mapping[str, PageId] = {
    "o": "overview",
    "c": "cloud",
    "t": "topology",
    "k": "knowledge",
    "w": "scheduler",
    "d": "twin",
    "g": "consensus",
    "r": "research",
    "h": "health",
}

PAGE_TITLES: Mapping[PageId, str] = {
    "overview": "Overview",
    "cloud": "Cloud Federation",
    "topology": "Topology",
    "knowledge": "Knowledge Graph",
    "scheduler": "Worldwide Scheduler",
    "twin": "Digital Twin",
    "consensus": "Global Consensus",
    "research": "Research",
    "health": "Health",
}

ViewFn = Callable[[HorizonSnapshot], RenderableType]


@dataclass(frozen=True, slots=True)
class HorizonRouter:
    """Immutable registry of page renderers keyed by ``PageId``."""

    views: Mapping[PageId, ViewFn]

    @staticmethod
    def default() -> HorizonRouter:
        return HorizonRouter(
            views={
                "overview": render_overview,
                "cloud": render_cloud,
                "topology": render_topology,
                "knowledge": render_knowledge,
                "scheduler": render_scheduler,
                "twin": render_twin,
                "consensus": render_consensus,
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
        snapshot: HorizonSnapshot,
        *,
        with_chrome: bool = True,
    ) -> RenderableType:
        """Render a page (optionally wrapped in Horizon chrome)."""

        if page not in self.views:
            raise KeyError(f"unknown horizon page: {page}")
        body = self.views[page](snapshot)
        if not with_chrome:
            return body
        return compose_frame(body, page=PAGE_TITLES[page])


def normalize_page(value: str) -> PageId:
    """Normalize a page name string to a ``PageId``."""

    lowered = value.strip().lower()
    aliases = {
        "cloud federation": "cloud",
        "cloud_federation": "cloud",
        "knowledge graph": "knowledge",
        "knowledge_graph": "knowledge",
        "worldwide scheduler": "scheduler",
        "planetary": "scheduler",
        "digital twin": "twin",
        "digital_twin": "twin",
        "global consensus": "consensus",
        "global_consensus": "consensus",
    }
    lowered = aliases.get(lowered, lowered)
    if lowered not in PAGE_IDS:
        raise ValueError(f"unknown page: {value}")
    return lowered  # type: ignore[return-value]
