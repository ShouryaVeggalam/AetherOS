"""Horizon MetricGrid — responsive columns of StatCard tiles.

Presentation layout helper. Never computes metrics itself.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from rich.columns import Columns
from rich.console import RenderableType

from aetheros.horizon.widgets.stat_card import StatCard


@dataclass(frozen=True, slots=True)
class MetricGrid:
    """Immutable grid of ``StatCard`` tiles."""

    cards: tuple[StatCard, ...]
    equal: bool = True
    expand: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "cards", tuple(self.cards))

    def __rich__(self) -> RenderableType:
        if not self.cards:
            return Columns([], equal=self.equal, expand=self.expand)
        return Columns(list(self.cards), equal=self.equal, expand=self.expand)


def metric_grid_from_pairs(
    pairs: Sequence[tuple[str, str]],
    *,
    tone: str = "bright_white",
) -> MetricGrid:
    """Build a ``MetricGrid`` from ``(label, value)`` pairs."""

    cards = tuple(
        StatCard(label=label, value=value, tone=tone) for label, value in pairs
    )
    return MetricGrid(cards=cards)
