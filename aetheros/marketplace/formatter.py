"""Rich formatter for the Extension Marketplace dashboard panel (shortcut E).

= remains Explainability. E opens Extensions marketplace views.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.marketplace.models import InstalledPlugin, PluginManifest
from aetheros.marketplace.updater import UpdateRecommendation


@dataclass(frozen=True, slots=True)
class MarketplacePanel:
    """Center-panel renderable for Extension Marketplace (shortcut E)."""

    catalog: tuple[PluginManifest, ...] = ()
    installed: tuple[InstalledPlugin, ...] = ()
    updates: tuple[UpdateRecommendation, ...] = ()
    selected: PluginManifest | None = None
    view: str = "marketplace"

    def __rich__(self) -> RenderableType:
        if not self.catalog and not self.installed:
            return Panel(
                Text(
                    "EXTENSION MARKETPLACE idle.\n"
                    "Discover · install · verify · enable sandboxed plugins.\n"
                    "No WRITE permissions · Plugin SDK sandbox by default.\n"
                    "@ opens this page · E opens Enterprise · = remains Explainability.\n"
                    "Status: Read-only catalog",
                    style="dim",
                ),
                title="Extension Marketplace",
                border_style="bright_yellow",
            )

        view = self.view.lower()
        if view == "installed":
            body = self._installed_view()
        elif view == "updates":
            body = self._updates_view()
        elif view == "permissions":
            body = self._permissions_view()
        elif view in {"details", "plugin", "plugin details"}:
            body = self._details_view()
        else:
            body = self._marketplace_view()
        return Panel(body, title="Extension Marketplace", border_style="bright_yellow")

    def _marketplace_view(self) -> RenderableType:
        enabled = sum(1 for p in self.installed if p.enabled)
        pending = sum(1 for u in self.updates if u.update_available)
        top = self.selected or (self.catalog[0] if self.catalog else None)
        parts: list[Text] = [
            Text("AETHEROS MARKETPLACE", style="bold bright_yellow"),
            Text(""),
            Text("Installed", style="bold"),
            Text(f"  {len(self.installed)}"),
            Text(""),
            Text("Enabled", style="bold"),
            Text(f"  {enabled}"),
            Text(""),
            Text("Updates", style="bold"),
            Text(f"  {pending}"),
            Text(""),
        ]
        if top is not None:
            parts.extend(
                [
                    Text("Top Plugin", style="bold"),
                    Text(f"  {top.name}"),
                    Text(""),
                    Text("Version", style="bold"),
                    Text(f"  {top.version}"),
                    Text(""),
                    Text("Permissions", style="bold"),
                ]
            )
            for perm in top.permissions:
                parts.append(Text(f"  {perm}"))
            if not top.permissions:
                parts.append(Text("  (none)", style="dim"))
            parts.extend(
                [
                    Text(""),
                    Text("Status", style="bold"),
                    Text("  Verified"),
                ]
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Marketplace  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _installed_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("AETHEROS MARKETPLACE", style="bold bright_yellow"),
            Text(""),
            Text("Installed", style="bold"),
            Text(""),
        ]
        if not self.installed:
            parts.append(Text("  (none)", style="dim"))
        for record in self.installed:
            flag = "on " if record.enabled else "off"
            upd = " · update" if record.update_available else ""
            parts.append(
                Text(
                    f"  · {record.manifest.name:<24} "
                    f"v{record.manifest.version}  [{flag}]{upd}"
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Installed  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _updates_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("AETHEROS MARKETPLACE", style="bold bright_yellow"),
            Text(""),
            Text("Updates", style="bold"),
            Text(""),
            Text("  Auto-update is disabled. Recommendations only.", style="dim"),
            Text(""),
        ]
        pending = [u for u in self.updates if u.update_available or u.deprecated]
        if not pending:
            parts.append(Text("  (none)", style="dim"))
        for tip in pending:
            avail = tip.available_version or "—"
            parts.append(
                Text(f"  · {tip.plugin_id:<22} " f"{tip.current_version} → {avail}")
            )
            parts.append(Text(f"      {tip.reason}", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Updates  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _permissions_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("AETHEROS MARKETPLACE", style="bold bright_yellow"),
            Text(""),
            Text("Permissions", style="bold"),
            Text(""),
            Text("  READ_GRAPH", style="green"),
            Text("  READ_CONTEXT", style="green"),
            Text("  READ_TELEMETRY", style="green"),
            Text("  READ_RESEARCH", style="green"),
            Text("  READ_SIMULATION", style="green"),
            Text(""),
            Text("  WRITE_*  — never allowed", style="red"),
            Text("  Sandbox by default", style="dim"),
            Text(""),
            Text("View", style="dim"),
            Text("  Permissions  (] cycles)"),
        ]
        return Group(*parts)

    def _details_view(self) -> RenderableType:
        plugin = self.selected
        if plugin is None and self.installed:
            plugin = self.installed[0].manifest
        if plugin is None and self.catalog:
            plugin = self.catalog[0]
        parts: list[Text] = [
            Text("AETHEROS MARKETPLACE", style="bold bright_yellow"),
            Text(""),
            Text("Plugin Details", style="bold"),
            Text(""),
        ]
        if plugin is None:
            parts.append(Text("  (none selected)", style="dim"))
        else:
            parts.extend(
                [
                    Text(f"  id          {plugin.id}"),
                    Text(f"  name        {plugin.name}"),
                    Text(f"  version     {plugin.version}"),
                    Text(f"  author      {plugin.author}"),
                    Text(f"  category    {plugin.category}"),
                    Text(f"  sdk         {plugin.sdk_version}"),
                    Text(f"  checksum    {plugin.checksum[:22]}…"),
                    Text(f"  description {plugin.description}"),
                    Text(""),
                    Text("  permissions:"),
                ]
            )
            for perm in plugin.permissions:
                parts.append(Text(f"    · {perm}"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Plugin Details  (] cycles)"),
            ]
        )
        return Group(*parts)
