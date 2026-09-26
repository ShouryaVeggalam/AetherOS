"""Rich formatter for Infrastructure Digital Twin (dashboard shortcut I).

~ remains Infinity. I opens Infrastructure Twin views.
Status always shows Simulation Only.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.infra_twin.models import (
    InfrastructureDiff,
    InfrastructureSnapshot,
    SimulationResult,
    TwinScenario,
)
from aetheros.infra_twin.simulator import TwinRun


@dataclass(frozen=True, slots=True)
class InfrastructureTwinPanel:
    """Center-panel renderable for Infrastructure Digital Twin (shortcut I)."""

    snapshot: InfrastructureSnapshot | None = None
    scenarios: tuple[TwinScenario, ...] = ()
    run: TwinRun | None = None
    view: str = "snapshot"

    def __rich__(self) -> RenderableType:
        if self.snapshot is None and self.run is None:
            return Panel(
                Text(
                    "INFRASTRUCTURE DIGITAL TWIN idle.\n"
                    "Clone → Scenario → Evaluate → Diff (simulation only).\n"
                    "Never mutates AWS · Azure · GCP · Kubernetes · Docker · Edge.\n"
                    "I opens this page · ~ remains Infinity.\n"
                    "Status: Simulation Only",
                    style="dim",
                ),
                title="Infrastructure Digital Twin",
                border_style="bright_magenta",
            )

        view = self.view.lower()
        if view in {"scenario", "scenarios", "library"}:
            body = self._library_view()
        elif view == "simulation":
            body = self._simulation_view()
        elif view == "diff":
            body = self._diff_view()
        elif view == "availability":
            body = self._availability_view()
        else:
            body = self._snapshot_view()
        return Panel(
            body, title="Infrastructure Digital Twin", border_style="bright_magenta"
        )

    def _snapshot_view(self) -> RenderableType:
        snap = self.snapshot or (self.run.baseline if self.run else None)
        assert snap is not None
        parts: list[Text] = [
            Text("INFRASTRUCTURE DIGITAL TWIN", style="bold bright_magenta"),
            Text(""),
            Text("Live Snapshot", style="bold"),
            Text(f"  {snap.id}"),
            Text(""),
            Text("Regions", style="bold"),
            Text(f"  {len(snap.regions)}"),
            Text(""),
            Text("Nodes", style="bold"),
            Text(f"  {snap.node_count} ({snap.available_nodes} available)"),
            Text(""),
            Text("Resources", style="bold"),
            Text(f"  {len(snap.resources)}"),
            Text(""),
            Text("Status", style="bold"),
            Text("  Simulation Only"),
            Text(""),
            Text("View", style="dim"),
            Text("  Live Snapshot  (] cycles)"),
        ]
        return Group(*parts)

    def _library_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("INFRASTRUCTURE DIGITAL TWIN", style="bold bright_magenta"),
            Text(""),
            Text("Scenario Library", style="bold"),
        ]
        for scenario in self.scenarios:
            parts.append(Text(f"  • {scenario.name}"))
            parts.append(Text(f"    {scenario.description}", style="dim"))
        if not self.scenarios:
            parts.append(Text("  (empty)", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("Status", style="bold"),
                Text("  Simulation Only"),
                Text(""),
                Text("View", style="dim"),
                Text("  Scenario Library  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _simulation_view(self) -> RenderableType:
        if self.run is None:
            return Group(
                Text("INFRASTRUCTURE DIGITAL TWIN", style="bold bright_magenta"),
                Text(""),
                Text("No simulation run yet.", style="dim"),
                Text("Status", style="bold"),
                Text("  Simulation Only"),
            )
        result = self.run.result
        scenario = self.run.scenario
        affected = len(self.run.diff.degraded)
        title = scenario.name.replace("_", " ").title()
        parts: list[Text] = [
            Text("INFRASTRUCTURE DIGITAL TWIN", style="bold bright_magenta"),
            Text(""),
            Text("Scenario", style="bold"),
            Text(f"  {title}"),
            Text(""),
            Text("Regions", style="bold"),
            Text(f"  {len(self.run.baseline.regions)}"),
            Text(""),
            Text("Affected", style="bold"),
            Text(f"  {affected}"),
            Text(""),
            Text("Availability", style="bold"),
            Text(f"  {result.availability:.2f}%"),
            Text(""),
            Text("Latency", style="bold"),
            Text(f"  {result.latency:.0f} ms"),
            Text(""),
            Text("Risk", style="bold"),
            Text(f"  {result.risk.title()}"),
            Text(""),
            Text("Confidence", style="bold"),
            Text(f"  {result.confidence:.0f}%"),
            Text(""),
            Text("Status", style="bold"),
            Text("  Simulation Only"),
            Text(""),
            Text("View", style="dim"),
            Text("  Simulation  (] cycles)"),
        ]
        return Group(*parts)

    def _diff_view(self) -> RenderableType:
        if self.run is None:
            return Text("No diff — run a scenario first.", style="dim")
        delta: InfrastructureDiff = self.run.diff
        parts: list[Text] = [
            Text("INFRASTRUCTURE DIGITAL TWIN", style="bold bright_magenta"),
            Text(""),
            Text("Diff", style="bold"),
            Text(""),
            Text("Nodes", style="bold"),
            Text(f"  {delta.nodes_before} → {delta.nodes_after}"),
            Text(""),
            Text("Latency", style="bold"),
            Text(f"  {delta.latency_before:.0f}ms → {delta.latency_after:.0f}ms"),
            Text(""),
            Text("Availability", style="bold"),
            Text(
                f"  {delta.availability_before:.2f}% → {delta.availability_after:.2f}%"
            ),
            Text(""),
            Text("Degraded", style="bold"),
            Text(f"  {len(delta.degraded)}"),
            Text(""),
            Text("Changed", style="bold"),
            Text(f"  {len(delta.changed)}"),
            Text(""),
            Text("Status", style="bold"),
            Text("  Simulation Only"),
            Text(""),
            Text("View", style="dim"),
            Text("  Diff  (] cycles)"),
        ]
        return Group(*parts)

    def _availability_view(self) -> RenderableType:
        result: SimulationResult | None = self.run.result if self.run else None
        snap = self.snapshot or (self.run.after if self.run else None)
        avail = (
            result.availability
            if result
            else (
                (100.0 * snap.available_nodes / snap.node_count)
                if snap and snap.node_count
                else 0.0
            )
        )
        parts: list[Text] = [
            Text("INFRASTRUCTURE DIGITAL TWIN", style="bold bright_magenta"),
            Text(""),
            Text("Availability", style="bold"),
            Text(f"  {avail:.2f}%"),
            Text(""),
        ]
        if result is not None:
            parts.extend(
                [
                    Text("Stability", style="bold"),
                    Text(f"  {result.stability:.1f}"),
                    Text(""),
                    Text("CPU util (proxy)", style="bold"),
                    Text(f"  {result.cpu:.1f}%"),
                    Text(""),
                    Text("Memory util (proxy)", style="bold"),
                    Text(f"  {result.memory:.1f}%"),
                    Text(""),
                    Text("Confidence", style="bold"),
                    Text(f"  {result.confidence:.0f}%"),
                    Text(""),
                    Text("Explanation", style="bold"),
                    Text(f"  {result.explanation}"),
                    Text(""),
                ]
            )
        parts.extend(
            [
                Text("Status", style="bold"),
                Text("  Simulation Only"),
                Text(""),
                Text("View", style="dim"),
                Text("  Availability  (] cycles)"),
            ]
        )
        return Group(*parts)
