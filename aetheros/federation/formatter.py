"""Rich formatter for the Federation Protocol dashboard panel (shortcut U).

F remains Fabric. U opens Federation Protocol views.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.federation.models import (
    PROTOCOL_VERSION,
    Heartbeat,
    NodeRecord,
    RegistryView,
)


@dataclass(frozen=True, slots=True)
class FederationPanel:
    """Center-panel renderable for Federation Protocol (shortcut U)."""

    registry: RegistryView | None = None
    heartbeats: tuple[Heartbeat, ...] = ()
    view: str = "nodes"
    last_sync: datetime | None = None

    def __rich__(self) -> RenderableType:
        if self.registry is None or not self.registry.nodes:
            return Panel(
                Text(
                    "FEDERATION idle.\n"
                    "Nodes publish immutable telemetry snapshots only.\n"
                    "No SSH · no remote execution · read-only protocol.\n"
                    "U opens this page · F remains Fabric.\n"
                    f"Protocol v{PROTOCOL_VERSION}",
                    style="dim",
                ),
                title="Federation Protocol",
                border_style="bright_cyan",
            )

        view = self.view.lower()
        if view == "registry":
            body = self._registry_view()
        elif view == "heartbeats":
            body = self._heartbeats_view()
        elif view == "protocol":
            body = self._protocol_view()
        else:
            body = self._nodes_view()
        return Panel(body, title="Federation Protocol", border_style="bright_cyan")

    def _nodes_view(self) -> RenderableType:
        reg = self.registry
        assert reg is not None
        sync = self._sync_label()
        status_label = {
            "healthy": "Healthy",
            "degraded": "Degraded",
            "empty": "Empty",
        }.get(reg.status, reg.status.title())
        parts: list[Text] = [
            Text("FEDERATION", style="bold bright_cyan"),
            Text(""),
            Text("Connected Nodes", style="bold"),
            Text(f"  {len(reg.nodes)}"),
            Text(""),
            Text("Online", style="bold"),
            Text(f"  {reg.online_count}"),
            Text(""),
            Text("Offline", style="bold"),
            Text(f"  {reg.offline_count}"),
            Text(""),
            Text("Protocol", style="bold"),
            Text(f"  v{reg.protocol_version.split('.')[0]}"),
            Text(""),
            Text("Last Sync", style="bold"),
            Text(f"  {sync}"),
            Text(""),
            Text("Status", style="bold"),
            Text(f"  {status_label}"),
            Text(""),
            Text("View", style="dim"),
            Text("  Connected Nodes  (] cycles)"),
        ]
        return Group(*parts)

    def _registry_view(self) -> RenderableType:
        reg = self.registry
        assert reg is not None
        parts: list[Text] = [
            Text("FEDERATION", style="bold bright_cyan"),
            Text(""),
            Text("Registry", style="bold"),
            Text(""),
        ]
        for record in reg.nodes[:12]:
            parts.append(Text(self._format_record(record)))
        if not reg.nodes:
            parts.append(Text("  (none)", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Registry  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _heartbeats_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("FEDERATION", style="bold bright_cyan"),
            Text(""),
            Text("Heartbeats", style="bold"),
            Text(""),
        ]
        beats = self.heartbeats
        if not beats and self.registry is not None:
            beats = tuple(
                r.last_heartbeat
                for r in self.registry.nodes
                if r.last_heartbeat is not None
            )
        if not beats:
            parts.append(Text("  (none)", style="dim"))
        for hb in beats[:12]:
            ts = hb.timestamp.astimezone(UTC).strftime("%H:%M:%S")
            batt = "—" if hb.battery is None else f"{hb.battery:.0f}%"
            parts.append(
                Text(
                    f"  {hb.node_id[:16]:<16} cpu={hb.cpu:5.1f} "
                    f"mem={hb.memory:5.1f} disk={hb.disk:5.1f} "
                    f"net={hb.network:5.1f} bat={batt} @ {ts}Z"
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Heartbeats  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _protocol_view(self) -> RenderableType:
        reg = self.registry
        assert reg is not None
        parts: list[Text] = [
            Text("FEDERATION", style="bold bright_cyan"),
            Text(""),
            Text("Protocol Version", style="bold"),
            Text(f"  {PROTOCOL_VERSION}"),
            Text(""),
            Text("Schema", style="bold"),
            Text("  heartbeat · snapshot · announce · goodbye"),
            Text(""),
            Text("Encoding", style="bold"),
            Text("  JSON · sorted keys · UTF-8 · no pickle"),
            Text(""),
            Text("Guarantees", style="bold"),
            Text("  read-only · immutable snapshots · no remote execution"),
            Text(""),
            Text("Node versions", style="bold"),
        ]
        versions = sorted({r.identity.version for r in reg.nodes})
        for ver in versions[:8]:
            parts.append(Text(f"  · {ver}"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Protocol Version  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _sync_label(self) -> str:
        stamp = self.last_sync
        if stamp is None and self.registry is not None:
            stamp = self.registry.last_seen
        if stamp is None:
            return "—"
        return stamp.astimezone(UTC).strftime("%H:%M:%S UTC")

    @staticmethod
    def _format_record(record: NodeRecord) -> str:
        ident = record.identity
        seen = record.last_seen.astimezone(UTC).strftime("%H:%M:%S")
        return (
            f"  · {ident.node_id[:18]:<18} {record.status:<8} "
            f"{ident.region:<10} v{ident.version} last={seen}Z"
        )
