"""Rich formatter for long-term operational memory."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.memory.models import MemoryRecord, Pattern


@dataclass(frozen=True, slots=True)
class OperationalMemoryPanel:
    """Center-panel renderable for operational memory (shortcut L)."""

    verified: tuple[MemoryRecord, ...] = ()
    patterns: tuple[Pattern, ...] = ()
    view: str = "verified"

    def __rich__(self) -> RenderableType:
        """Render verified pattern summary matching the P2 Rich example."""

        if not self.verified and not self.patterns:
            return Panel(
                Text(
                    "OPERATIONAL MEMORY idle.\n"
                    "Seed or ingest verified system patterns only.\n"
                    "No conversations · no personal data.\n"
                    "L opens this page · M remains Multi-Agent.\n"
                    "Status: Verified knowledge only",
                    style="dim",
                ),
                title="Operational Memory",
                border_style="bright_green",
            )

        view = self.view.lower()
        if view == "recent":
            body = self._recent_discoveries()
        elif view == "related":
            body = self._related_patterns()
        elif view == "timeline":
            body = self._evidence_timeline()
        else:
            body = self._verified_summary()

        return Panel(
            body,
            title="Operational Memory",
            border_style="bright_green",
        )

    def _verified_summary(self) -> RenderableType:
        top = self.verified[0] if self.verified else None
        pattern = self.patterns[0] if self.patterns else None
        parts: list[Text] = [
            Text("OPERATIONAL MEMORY", style="bold bright_green"),
            Text(""),
            Text("Verified Patterns", style="bold"),
            Text(f"  {len(self.verified)}"),
            Text(""),
        ]
        if top is not None:
            parts.extend(
                [
                    Text("Top Pattern", style="bold"),
                    Text(f"  {top.title}"),
                    Text(""),
                    Text("Occurrences", style="bold"),
                    Text(f"  {top.evidence_count}"),
                    Text(""),
                    Text("Confidence", style="bold"),
                    Text(f"  {top.confidence:.0f}%"),
                    Text(""),
                    Text("Evidence", style="bold"),
                    Text(f"  {', '.join(top.sources) or 'Telemetry'}"),
                    Text(""),
                ]
            )
        elif pattern is not None:
            parts.extend(
                [
                    Text("Top Pattern", style="bold"),
                    Text(f"  {pattern.label}"),
                    Text(""),
                    Text("Occurrences", style="bold"),
                    Text(f"  {pattern.occurrences}"),
                    Text(""),
                    Text("Confidence", style="bold"),
                    Text(f"  {pattern.confidence:.0f}%"),
                    Text(""),
                ]
            )
        parts.extend(
            [
                Text("Reasoning", style="bold"),
                Text("  Verified"),
                Text(""),
                Text("Simulation", style="bold"),
                Text("  Supported when present in sources"),
                Text(""),
                Text("Status", style="bold"),
                Text("  Verified"),
                Text(""),
                Text("View", style="dim"),
                Text("  Verified Memories  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _recent_discoveries(self) -> RenderableType:
        parts: list[Text] = [
            Text("OPERATIONAL MEMORY", style="bold bright_green"),
            Text(""),
            Text("Recent Discoveries", style="bold"),
            Text(""),
        ]
        recent = sorted(
            self.verified,
            key=lambda r: r.last_verified,
            reverse=True,
        )[:8]
        if not recent:
            parts.append(Text("  (none)", style="dim"))
        for record in recent:
            parts.append(
                Text(
                    f"  · {record.title}  "
                    f"({record.confidence:.0f}% · {record.evidence_count} ev)",
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Recent Discoveries  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _related_patterns(self) -> RenderableType:
        parts: list[Text] = [
            Text("OPERATIONAL MEMORY", style="bold bright_green"),
            Text(""),
            Text("Related Patterns", style="bold"),
            Text(""),
        ]
        if not self.patterns:
            parts.append(Text("  (none)", style="dim"))
        for pattern in self.patterns[:8]:
            parts.append(
                Text(
                    f"  · {pattern.label}  "
                    f"sim={pattern.similarity:.0f}%  "
                    f"n={pattern.occurrences}  "
                    f"conf={pattern.confidence:.0f}%",
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Related Patterns  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _evidence_timeline(self) -> RenderableType:
        parts: list[Text] = [
            Text("OPERATIONAL MEMORY", style="bold bright_green"),
            Text(""),
            Text("Evidence Timeline", style="bold"),
            Text(""),
        ]
        ordered = sorted(self.verified, key=lambda r: r.created_at)
        if not ordered:
            parts.append(Text("  (none)", style="dim"))
        for record in ordered[:10]:
            stamp = record.last_verified.strftime("%Y-%m-%d %H:%M")
            sources = ", ".join(record.sources) or "telemetry"
            parts.append(Text(f"  {stamp}  {record.title}"))
            parts.append(
                Text(
                    f"           evidence={record.evidence_count}  "
                    f"sources={sources}",
                    style="dim",
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Evidence Timeline  (] cycles)"),
            ]
        )
        return Group(*parts)
