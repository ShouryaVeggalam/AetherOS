"""Horizon widget kit — reusable Rich presentation primitives."""

from __future__ import annotations

from aetheros.horizon.widgets.metric_grid import MetricGrid, metric_grid_from_pairs
from aetheros.horizon.widgets.sparkline import HorizonSparkline, render_sparkline
from aetheros.horizon.widgets.stat_card import StatCard
from aetheros.horizon.widgets.table import HorizonTable
from aetheros.horizon.widgets.timeline import Timeline, timeline_from_pairs
from aetheros.horizon.widgets.tree import HorizonTree, TreeNodeSpec, tree_from_paths

__all__ = [
    "HorizonSparkline",
    "HorizonTable",
    "HorizonTree",
    "MetricGrid",
    "StatCard",
    "Timeline",
    "TreeNodeSpec",
    "metric_grid_from_pairs",
    "render_sparkline",
    "timeline_from_pairs",
    "tree_from_paths",
]
