"""Horizon Timeline — vertical event list for research / simulation history.

Presentation only. Renders labeled stamps; never appends to journals.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.text import Text


@dataclass(frozen=True, slots=True)
class Timeline:
    """Immutable vertical timeline of ``(stamp, message)`` events."""

    events: tuple[tuple[str, str], ...] = ()
    empty_label: str = "(no events)"

    def __post_init__(self) -> None:
        object.__setattr__(self, "events", tuple(self.events))

    def __rich__(self) -> RenderableType:
        if not self.events:
            return Text(f"  {self.empty_label}", style="dim")
        parts: list[Text] = []
        for stamp, message in self.events:
            parts.append(Text.assemble((f"  {stamp}  ", "dim"), (message, "")))
        return Group(*parts)


def timeline_from_pairs(pairs: Sequence[tuple[str, str]]) -> Timeline:
    """Build a ``Timeline`` from stamp/message pairs."""

    return Timeline(events=tuple((str(a), str(b)) for a, b in pairs))
