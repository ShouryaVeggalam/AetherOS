"""Rich formatter for P4 Multi-Agent Consensus (dashboard shortcut J)."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.agents.base import Conflict, ConsensusFinding
from aetheros.agents.coordinator import ConsensusDecision
from aetheros.agents.events import Event


@dataclass(frozen=True, slots=True)
class ConsensusPanel:
    """Center-panel renderable for multi-agent consensus (shortcut J)."""

    findings: tuple[ConsensusFinding, ...] = ()
    decision: ConsensusDecision | None = None
    conflicts: tuple[Conflict, ...] = ()
    bus_events: tuple[Event, ...] = ()
    view: str = "consensus"

    def __rich__(self) -> RenderableType:
        if self.decision is None and not self.findings:
            return Panel(
                Text(
                    "MULTI-AGENT CONSENSUS idle.\n"
                    "Specialists analyze evidence independently.\n"
                    "Coordinator merges outputs — never executes.\n"
                    "J opens this page · M remains Multi-Agent · A remains Research.\n"
                    "Status: Human Approval Required",
                    style="dim",
                ),
                title="Multi-Agent Consensus",
                border_style="bright_magenta",
            )

        view = self.view.lower()
        if view == "status":
            body = self._status_view()
        elif view == "findings":
            body = self._findings_view()
        elif view == "bus":
            body = self._bus_view()
        elif view == "conflicts":
            body = self._conflicts_view()
        else:
            body = self._consensus_view()

        return Panel(
            body,
            title="Multi-Agent Consensus",
            border_style="bright_magenta",
        )

    def _finding_map(self) -> dict[str, ConsensusFinding]:
        return {f.agent: f for f in self.findings}

    def _status_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("MULTI-AGENT CONSENSUS", style="bold bright_magenta"),
            Text(""),
            Text("Agent Status", style="bold"),
            Text(""),
        ]
        if not self.findings:
            parts.append(Text("  (none)", style="dim"))
        for finding in self.findings:
            parts.append(
                Text(
                    f"  · {finding.agent}: {finding.summary[:60]}  "
                    f"({finding.confidence:.0f}%)"
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Agent Status  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _findings_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("MULTI-AGENT CONSENSUS", style="bold bright_magenta"),
            Text(""),
            Text("Live Findings", style="bold"),
            Text(""),
        ]
        if not self.findings:
            parts.append(Text("  (none)", style="dim"))
        for finding in self.findings:
            parts.append(Text(f"  {finding.agent}", style="bold"))
            parts.append(Text(f"    {finding.summary}"))
            for ev in finding.evidence[:3]:
                parts.append(Text(f"    · {ev}", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Live Findings  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _bus_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("MULTI-AGENT CONSENSUS", style="bold bright_magenta"),
            Text(""),
            Text("Message Bus", style="bold"),
            Text(""),
        ]
        if not self.bus_events:
            parts.append(Text("  (empty)", style="dim"))
        for event in self.bus_events[-12:]:
            parts.append(
                Text(
                    f"  {event.sender} → {event.receiver}  [{event.type}]",
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Message Bus  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _conflicts_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("MULTI-AGENT CONSENSUS", style="bold bright_magenta"),
            Text(""),
            Text("Conflicts", style="bold"),
            Text(""),
        ]
        if not self.conflicts:
            parts.append(Text("  (none)", style="dim"))
        for conflict in self.conflicts:
            parts.append(Text(f"  {conflict.source} ↔ {conflict.target}"))
            parts.append(Text(f"    {conflict.disagreement}", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Conflicts  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _consensus_view(self) -> RenderableType:
        by_agent = self._finding_map()
        parts: list[Text] = [
            Text("MULTI-AGENT CONSENSUS", style="bold bright_magenta"),
            Text(""),
        ]
        for label, key, fallback in (
            ("Telemetry", "telemetry", "Idle"),
            ("Performance", "performance", "Idle"),
            ("Battery", "battery", "Idle"),
            ("Security", "security", "Idle"),
            ("Research", "research", "Idle"),
        ):
            finding = by_agent.get(key)
            parts.append(Text(label, style="bold"))
            parts.append(Text(f"  {finding.summary if finding else fallback}"))
            parts.append(Text(""))

        parts.append(Text("Coordinator", style="bold"))
        if self.decision is None:
            parts.append(Text("  Awaiting findings", style="dim"))
        else:
            parts.extend(
                [
                    Text(""),
                    Text("Recommendation", style="bold"),
                    Text(f"  {self.decision.recommendation}"),
                    Text(""),
                    Text("Confidence", style="bold"),
                    Text(f"  {self.decision.confidence:.0f}%"),
                    Text(""),
                    Text("Supporting Agents", style="bold"),
                    Text(
                        "  " + (", ".join(self.decision.supporting_agents) or "(none)")
                    ),
                    Text(""),
                    Text("Reasoning", style="bold"),
                    Text(f"  {self.decision.reasoning}"),
                    Text(""),
                    Text("Status", style="bold"),
                    Text("  Human Approval Required"),
                ]
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Consensus  (] cycles)"),
            ]
        )
        return Group(*parts)
