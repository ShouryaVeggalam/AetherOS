"""Rich plugin inspector — read-only view of loaded / rejected plugins.

Presentation only. Never enables, disables, or executes plugins.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from plugins.sdk.loader import LoadedPlugin, RejectedPlugin
from plugins.sdk.version import SDK_VERSION


@dataclass(frozen=True, slots=True)
class PluginInspector:
    """Rich inspector for Plugin SDK sessions."""

    loaded: tuple[LoadedPlugin, ...] = ()
    rejected: tuple[RejectedPlugin, ...] = ()
    title: str = "Plugin SDK Inspector"

    def __rich__(self) -> RenderableType:
        table = Table(
            show_header=True,
            expand=True,
            box=None,
            header_style="bold dim",
            padding=(0, 1),
        )
        table.add_column("ID")
        table.add_column("Version")
        table.add_column("Status")
        table.add_column("Capabilities")
        table.add_column("Detail")

        for item in self.loaded:
            table.add_row(
                item.manifest.id,
                item.manifest.version,
                "verified",
                ", ".join(item.manifest.capabilities) or "—",
                item.sandbox.reason,
            )
        for item in self.rejected:
            name = item.path.name
            table.add_row(
                name,
                "—",
                "rejected",
                "—",
                item.reason,
            )

        body = Group(
            Text("PLUGIN SDK", style="bold bright_cyan"),
            Text(
                f"SDK {SDK_VERSION} · sandboxed · read-only graph/context", style="dim"
            ),
            Text(""),
            (
                table
                if (self.loaded or self.rejected)
                else Text("  (no plugins)", style="dim")
            ),
            Text(""),
            Text(
                f"Loaded {len(self.loaded)} · Rejected {len(self.rejected)}",
                style="dim",
            ),
        )
        return Panel(body, title=self.title, border_style="bright_cyan")


def inspect_plugins(
    results: Sequence[LoadedPlugin | RejectedPlugin],
) -> PluginInspector:
    """Split mixed loader results into an inspector renderable."""

    loaded = tuple(r for r in results if isinstance(r, LoadedPlugin))
    rejected = tuple(r for r in results if isinstance(r, RejectedPlugin))
    return PluginInspector(loaded=loaded, rejected=rejected)
