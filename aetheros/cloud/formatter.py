"""Rich formatter for Cloud Federation Engine (dashboard shortcut C).

; remains Cluster overview. C opens Cloud Federation views.
Read-only status is always surfaced.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.cloud.models import (
    FederationHealth,
    InfrastructureSnapshot,
    ProviderRecord,
)


@dataclass(frozen=True, slots=True)
class CloudFederationPanel:
    """Center-panel renderable for Cloud Federation (shortcut C)."""

    snapshot: InfrastructureSnapshot | None = None
    health: FederationHealth | None = None
    records: tuple[ProviderRecord, ...] = ()
    snapshot_age_seconds: float = 0.0
    view: str = "providers"

    def __rich__(self) -> RenderableType:
        if self.snapshot is None:
            return Panel(
                Text(
                    "CLOUD FEDERATION idle.\n"
                    "AWS · Azure · GCP · Kubernetes · Docker · Edge.\n"
                    "Observation only — never provision / mutate.\n"
                    "C opens this page · ; remains Cluster overview.\n"
                    "Status: Read Only",
                    style="dim",
                ),
                title="Cloud Federation",
                border_style="bright_cyan",
            )

        view = self.view.lower()
        if view == "regions":
            body = self._regions_view()
        elif view == "resources":
            body = self._resources_view()
        elif view == "health":
            body = self._health_view()
        elif view == "snapshots":
            body = self._snapshots_view()
        else:
            body = self._providers_view()
        return Panel(body, title="Cloud Federation", border_style="bright_cyan")

    def _summary_header(self) -> list[Text]:
        assert self.snapshot is not None
        age = int(round(self.snapshot_age_seconds))
        return [
            Text("CLOUD FEDERATION", style="bold bright_cyan"),
            Text(""),
            Text("Providers", style="bold"),
            Text(f"  {self.snapshot.provider_count}"),
            Text(""),
            Text("Regions", style="bold"),
            Text(f"  {len(self.snapshot.regions)}"),
            Text(""),
            Text("Resources", style="bold"),
            Text(f"  {self.snapshot.resource_count}"),
            Text(""),
            Text("Snapshot Age", style="bold"),
            Text(f"  {age}s"),
            Text(""),
            Text("Status", style="bold"),
            Text("  Read Only"),
        ]

    def _provider_status_lines(self) -> list[Text]:
        lines: list[Text] = []
        by_name = {r.provider.name: r for r in self.records}
        for label in ("Kubernetes", "AWS", "Azure", "Google Cloud", "Docker", "Edge"):
            record = by_name.get(label)
            status = "Healthy"
            if record is None:
                status = "—"
            elif record.status == "degraded":
                status = "Degraded"
            elif record.status == "offline":
                status = "Offline"
            elif record.status == "unknown":
                status = "Unknown"
            lines.append(Text(label, style="bold"))
            lines.append(Text(f"  {status}"))
            lines.append(Text(""))
        return lines

    def _providers_view(self) -> RenderableType:
        parts = self._summary_header()
        parts.append(Text(""))
        parts.extend(self._provider_status_lines())
        parts.append(Text("View", style="dim"))
        parts.append(Text("  Providers  (] cycles)"))
        return Group(*parts)

    def _regions_view(self) -> RenderableType:
        assert self.snapshot is not None
        parts: list[Text] = [
            Text("CLOUD FEDERATION", style="bold bright_cyan"),
            Text(""),
            Text("Regions", style="bold"),
        ]
        for region in self.snapshot.regions:
            parts.append(Text(f"  {region}"))
        parts.extend(
            [
                Text(""),
                Text("Count", style="bold"),
                Text(f"  {len(self.snapshot.regions)}"),
                Text(""),
                Text("Status", style="bold"),
                Text("  Read Only"),
                Text(""),
                Text("View", style="dim"),
                Text("  Regions  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _resources_view(self) -> RenderableType:
        assert self.snapshot is not None
        parts: list[Text] = [
            Text("CLOUD FEDERATION", style="bold bright_cyan"),
            Text(""),
            Text("Resources", style="bold"),
            Text(f"  {self.snapshot.resource_count} total"),
            Text(""),
        ]
        # Group counts by provider.
        counts: dict[str, int] = {}
        for resource in self.snapshot.resources:
            counts[resource.provider] = counts.get(resource.provider, 0) + 1
        for provider, count in sorted(counts.items()):
            parts.append(Text(f"  {provider}: {count}"))
        parts.extend(
            [
                Text(""),
                Text("Sample", style="bold"),
            ]
        )
        for resource in self.snapshot.resources[:8]:
            parts.append(
                Text(f"  [{resource.provider}] {resource.type} {resource.name}")
            )
        parts.extend(
            [
                Text(""),
                Text("Status", style="bold"),
                Text("  Read Only"),
                Text(""),
                Text("View", style="dim"),
                Text("  Resources  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _health_view(self) -> RenderableType:
        health = self.health
        online = health.online if health else 0
        degraded = health.degraded if health else 0
        offline = health.offline if health else 0
        confidence = health.confidence if health else 0.0
        label = health.label if health else "offline"
        parts: list[Text] = [
            Text("CLOUD FEDERATION", style="bold bright_cyan"),
            Text(""),
            Text("Health", style="bold"),
            Text(f"  {label}"),
            Text(""),
            Text("Online", style="bold"),
            Text(f"  {online}"),
            Text(""),
            Text("Degraded", style="bold"),
            Text(f"  {degraded}"),
            Text(""),
            Text("Offline", style="bold"),
            Text(f"  {offline}"),
            Text(""),
            Text("Confidence", style="bold"),
            Text(f"  {confidence:.2f}"),
            Text(""),
        ]
        parts.extend(self._provider_status_lines())
        parts.extend(
            [
                Text("Status", style="bold"),
                Text("  Read Only"),
                Text(""),
                Text("View", style="dim"),
                Text("  Health  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _snapshots_view(self) -> RenderableType:
        assert self.snapshot is not None
        age = int(round(self.snapshot_age_seconds))
        parts: list[Text] = [
            Text("CLOUD FEDERATION", style="bold bright_cyan"),
            Text(""),
            Text("Snapshots", style="bold"),
            Text("  1 active (immutable)"),
            Text(""),
            Text("Timestamp", style="bold"),
            Text(f"  {self.snapshot.timestamp.isoformat()}"),
            Text(""),
            Text("Topology Hash", style="bold"),
            Text(f"  {self.snapshot.topology_hash[:48]}…"),
            Text(""),
            Text("Age", style="bold"),
            Text(f"  {age}s"),
            Text(""),
            Text("Export", style="bold"),
            Text("  JSON only (no pickle)"),
            Text(""),
            Text("Status", style="bold"),
            Text("  Read Only"),
            Text(""),
            Text("View", style="dim"),
            Text("  Snapshots  (] cycles)"),
        ]
        return Group(*parts)
