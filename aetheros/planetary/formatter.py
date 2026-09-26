"""Rich formatter for Planetary Scheduler (dashboard shortcut W).

% remaps to Workload Planner. W opens Worldwide / Planetary Scheduler.
Status is always Simulation Only — recommendations never deploy.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.planetary.models import GlobalWorkload, ScheduleDecision
from aetheros.planetary.optimizer import explain_trade_offs


@dataclass(frozen=True, slots=True)
class PlanetarySchedulerPanel:
    """Center-panel renderable for Planetary Scheduler (shortcut W)."""

    workload: GlobalWorkload | None = None
    decision: ScheduleDecision | None = None
    view: str = "map"

    def __rich__(self) -> RenderableType:
        if self.workload is None or self.decision is None:
            return Panel(
                Text(
                    "PLANETARY SCHEDULER idle.\n"
                    "Predicts optimal region → datacenter → cluster → node.\n"
                    "Infrastructure Digital Twin simulations only.\n"
                    "No Kubernetes · no cloud provisioning · no Terraform.\n"
                    "W opens this page · % opens Workload Planner.\n"
                    "Status: Simulation Only",
                    style="dim",
                ),
                title="Planetary Scheduler",
                border_style="bright_cyan",
            )

        view = self.view.lower()
        if view == "regions":
            body = self._regions_view()
        elif view == "candidates":
            body = self._candidates_view()
        elif view in ("tradeoffs", "trade-offs"):
            body = self._tradeoffs_view()
        elif view in ("simulation", "results"):
            body = self._simulation_view()
        else:
            body = self._map_view()
        return Panel(body, title="Planetary Scheduler", border_style="bright_cyan")

    def _map_view(self) -> RenderableType:
        assert self.workload is not None and self.decision is not None
        best = self.decision.best_candidate
        parts: list[Text] = [
            Text("PLANETARY SCHEDULER", style="bold bright_cyan"),
            Text(""),
            Text("Workload", style="bold"),
            Text(f"  {self.workload.name}"),
            Text(""),
            Text("Best Region", style="bold"),
            Text(f"  {best.region if best else '—'}"),
            Text(""),
            Text("Cluster", style="bold"),
            Text(f"  {best.cluster if best else '—'}"),
            Text(""),
            Text("Latency", style="bold"),
            Text(f"  {best.latency_ms:.0f} ms" if best else "  —"),
            Text(""),
            Text("Availability", style="bold"),
            Text(f"  {best.availability:.2f}%" if best else "  —"),
            Text(""),
            Text("Confidence", style="bold"),
            Text(f"  {self.decision.confidence:.0f}%"),
            Text(""),
            Text("Status", style="bold"),
            Text("  Simulation Only"),
            Text(""),
            Text("View", style="dim"),
            Text("  Global Map (logical)  (] cycles)"),
        ]
        return Group(*parts)

    def _regions_view(self) -> RenderableType:
        assert self.decision is not None
        parts: list[Text] = [
            Text("PLANETARY SCHEDULER", style="bold bright_cyan"),
            Text(""),
            Text("Regions", style="bold"),
            Text(""),
        ]
        ranked = self._ranked()
        regions = sorted({c.region for c in ranked})
        if not regions:
            parts.append(Text("  (none)", style="dim"))
        for region in regions:
            sites = [c for c in ranked if c.region == region]
            best = max(sites, key=lambda c: c.score)
            parts.append(
                Text(
                    f"  · {region:<18} best={best.cluster}/{best.node} "
                    f"score={best.score:.1f}"
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Regions  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _candidates_view(self) -> RenderableType:
        assert self.decision is not None
        parts: list[Text] = [
            Text("PLANETARY SCHEDULER", style="bold bright_cyan"),
            Text(""),
            Text("Candidates", style="bold"),
            Text(""),
        ]
        ranked = self._ranked()
        if not ranked:
            parts.append(Text("  (none)", style="dim"))
        for i, cand in enumerate(ranked, start=1):
            letter = chr(ord("A") + i - 1)
            parts.append(
                Text(
                    f"  {letter}. {cand.region}/{cand.cluster}/{cand.node}  "
                    f"score={cand.score:.1f}"
                )
            )
            if cand.trade_off:
                parts.append(Text(f"     {cand.trade_off}", style="dim"))
        if self.decision.rejected:
            parts.append(Text(""))
            parts.append(Text("Rejected", style="bold"))
            for site_id, reason in self.decision.rejected[:8]:
                parts.append(Text(f"  · {site_id}: {reason}", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Candidates  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _tradeoffs_view(self) -> RenderableType:
        assert self.decision is not None
        parts: list[Text] = [
            Text("PLANETARY SCHEDULER", style="bold bright_cyan"),
            Text(""),
            Text("Trade-offs", style="bold"),
            Text(""),
        ]
        lines = explain_trade_offs(self._ranked())
        if not lines:
            parts.append(Text("  (none)", style="dim"))
        for line in lines:
            parts.append(Text(f"  · {line}"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Trade-offs  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _simulation_view(self) -> RenderableType:
        assert self.decision is not None
        parts: list[Text] = [
            Text("PLANETARY SCHEDULER", style="bold bright_cyan"),
            Text(""),
            Text("Simulation Results", style="bold"),
            Text(""),
        ]
        if not self.decision.simulations:
            parts.append(Text("  (none)", style="dim"))
        for sim in self.decision.simulations[:8]:
            parts.append(
                Text(
                    f"  · {sim.site_id:<40} "
                    f"lat={sim.latency_ms:.1f}ms avail={sim.availability:.2f}% "
                    f"cpu={sim.cpu:.0f} mem={sim.memory:.0f} "
                    f"res={sim.failure_resilience:.0f}"
                )
            )
        parts.extend(
            [
                Text(""),
                Text(f"Confidence      {self.decision.confidence:.0f}%"),
                Text("Status          Simulation Only"),
                Text(""),
                Text("View", style="dim"),
                Text("  Simulation Results  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _ranked(self) -> tuple:
        assert self.decision is not None
        if self.decision.best_candidate is None:
            return ()
        return (self.decision.best_candidate, *self.decision.alternatives)
