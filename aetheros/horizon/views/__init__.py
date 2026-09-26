"""Horizon Observatory views — page renderers for the modular router."""

from __future__ import annotations

from aetheros.horizon.views.cloud import render_cloud
from aetheros.horizon.views.consensus import render_consensus
from aetheros.horizon.views.health import render_health
from aetheros.horizon.views.knowledge import render_knowledge
from aetheros.horizon.views.overview import render_overview
from aetheros.horizon.views.research import render_research
from aetheros.horizon.views.scheduler import render_scheduler
from aetheros.horizon.views.topology import render_topology
from aetheros.horizon.views.twin import render_twin

__all__ = [
    "render_cloud",
    "render_consensus",
    "render_health",
    "render_knowledge",
    "render_overview",
    "render_research",
    "render_scheduler",
    "render_topology",
    "render_twin",
]
