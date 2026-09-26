"""Atlas Table — thin Rich Table factory for registry / score grids.

Presentation only. Accepts row tuples; never queries backends.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import RenderableType
from rich.table import Table


@dataclass(frozen=True, slots=True)
class AtlasTable:
    """Immutable Rich Table with fixed columns and string rows."""

    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...] = ()
    title: str = ""
    show_header: bool = True
    box_none: bool = True

    def __post_init__(self) -> None:
        if not self.columns:
            raise ValueError("columns must be non-empty")
        width = len(self.columns)
        for row in self.rows:
            if len(row) != width:
                raise ValueError("row width must match columns")

    def __rich__(self) -> RenderableType:
        from rich import box

        table = Table(
            title=self.title or None,
            show_header=self.show_header,
            expand=True,
            box=None if self.box_none else box.SIMPLE,
            header_style="bold dim",
            padding=(0, 1),
        )
        for col in self.columns:
            table.add_column(col)
        for row in self.rows:
            table.add_row(*row)
        return table
