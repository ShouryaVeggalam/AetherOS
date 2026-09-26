"""Atlas widget kit — reusable Rich presentation primitives."""

from __future__ import annotations

from aetheros.atlas.widgets.progress_bar import AtlasProgressBar
from aetheros.atlas.widgets.sparkline import AtlasSparkline, render_sparkline
from aetheros.atlas.widgets.stat_card import StatCard
from aetheros.atlas.widgets.table import AtlasTable
from aetheros.atlas.widgets.tree import AtlasTree, TreeNodeSpec, tree_from_paths

__all__ = [
    "AtlasProgressBar",
    "AtlasSparkline",
    "AtlasTable",
    "AtlasTree",
    "StatCard",
    "TreeNodeSpec",
    "render_sparkline",
    "tree_from_paths",
]
