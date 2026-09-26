"""Atlas views — page renderers for the modular router."""

from __future__ import annotations

from aetheros.atlas.views.consensus import render_consensus
from aetheros.atlas.views.federation import render_federation
from aetheros.atlas.views.health import render_health
from aetheros.atlas.views.overview import render_overview
from aetheros.atlas.views.research import render_research
from aetheros.atlas.views.scheduler import render_scheduler
from aetheros.atlas.views.topology import render_topology
from aetheros.atlas.views.twin import render_twin

__all__ = [
    "render_consensus",
    "render_federation",
    "render_health",
    "render_overview",
    "render_research",
    "render_scheduler",
    "render_topology",
    "render_twin",
]
