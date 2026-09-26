"""Rich formatter for Distributed Scheduler (dashboard shortcut /).

S remains Sentinel. / opens Scheduler simulation views.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.scheduler.models import ScheduleResult, Workload


@dataclass(frozen=True, slots=True)
class SchedulerPanel:
    """Center-panel renderable for Distributed Scheduler (shortcut /)."""

    workload: Workload | None = None
    result: ScheduleResult | None = None
    view: str = "summary"

    def __rich__(self) -> RenderableType:
        if self.workload is None or self.result is None:
            return Panel(
                Text(
                    "DISTRIBUTED SCHEDULER idle.\n"
                    "Simulates placement on Digital Twin clones only.\n"
                    "No SSH · no Kubernetes · no Docker · never executes workloads.\n"
                    "/ opens this page · S remains Sentinel.\n"
                    "Status: Simulation Only",
                    style="dim",
                ),
                title="Distributed Scheduler",
                border_style="bright_magenta",
            )

        view = self.view.lower()
        if view == "workloads":
            body = self._workloads_view()
        elif view == "candidates":
            body = self._candidates_view()
        elif view == "scores":
            body = self._scores_view()
        elif view == "simulation":
            body = self._simulation_view()
        elif view == "tradeoffs":
            body = self._tradeoffs_view()
        else:
            body = self._summary_view()
        return Panel(body, title="Distributed Scheduler", border_style="bright_magenta")

    def _summary_view(self) -> RenderableType:
        assert self.workload is not None and self.result is not None
        best = self.result.best_plan
        candidates = "  ".join(p.target_node for p in self.result.plans) or "—"
        parts: list[Text] = [
            Text("DISTRIBUTED SCHEDULER", style="bold bright_magenta"),
            Text(""),
            Text("Workload", style="bold"),
            Text(f"  {self.workload.name}"),
            Text(""),
            Text("Candidate Nodes", style="bold"),
            Text(f"  {candidates}"),
            Text(""),
            Text("Best Plan", style="bold"),
            Text(f"  {best.target_node if best else '—'}"),
            Text(""),
            Text("Predicted CPU", style="bold"),
            Text(f"  {best.predicted_cpu:.0f}%" if best else "  —"),
            Text(""),
            Text("Latency", style="bold"),
            Text(f"  {best.predicted_latency_ms:.0f} ms" if best else "  —"),
            Text(""),
            Text("Confidence", style="bold"),
            Text(f"  {self.result.confidence:.0f}%"),
            Text(""),
            Text("Status", style="bold"),
            Text("  Simulation Only"),
            Text(""),
            Text("View", style="dim"),
            Text("  Summary  (] cycles)"),
        ]
        return Group(*parts)

    def _workloads_view(self) -> RenderableType:
        assert self.workload is not None
        w = self.workload
        parts = [
            Text("DISTRIBUTED SCHEDULER", style="bold bright_magenta"),
            Text(""),
            Text("Workloads", style="bold"),
            Text(""),
            Text(f"  · {w.name}  id={w.id}"),
            Text(
                f"    cpu={w.cpu_request:.0f} mem={w.memory_request:.0f} "
                f"gpu={w.gpu_request:.0f} priority={w.priority:.0f}"
            ),
            Text(""),
            Text("View", style="dim"),
            Text("  Workloads  (] cycles)"),
        ]
        return Group(*parts)

    def _candidates_view(self) -> RenderableType:
        assert self.result is not None
        parts: list[Text] = [
            Text("DISTRIBUTED SCHEDULER", style="bold bright_magenta"),
            Text(""),
            Text("Candidates", style="bold"),
            Text(""),
        ]
        if not self.result.plans:
            parts.append(Text("  (none)", style="dim"))
        for i, plan in enumerate(self.result.plans, start=1):
            parts.append(Text(f"  {i}. {plan.target_node:<20} score={plan.score:.1f}"))
        if self.result.rejected:
            parts.append(Text(""))
            parts.append(Text("Rejected", style="bold"))
            for node_id, reason in self.result.rejected[:8]:
                parts.append(Text(f"  · {node_id}: {reason}", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Candidates  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _scores_view(self) -> RenderableType:
        assert self.result is not None
        parts: list[Text] = [
            Text("DISTRIBUTED SCHEDULER", style="bold bright_magenta"),
            Text(""),
            Text("Scores", style="bold"),
            Text(""),
        ]
        for plan in self.result.plans:
            parts.append(Text(f"  · {plan.target_node}: {plan.score:.1f}"))
            parts.append(Text(f"    {plan.reasoning}", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Scores  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _simulation_view(self) -> RenderableType:
        assert self.result is not None
        parts: list[Text] = [
            Text("DISTRIBUTED SCHEDULER", style="bold bright_magenta"),
            Text(""),
            Text("Simulation", style="bold"),
            Text(""),
        ]
        for plan in self.result.plans:
            parts.append(
                Text(
                    f"  · {plan.target_node:<18} cpu={plan.predicted_cpu:.0f}% "
                    f"mem={plan.predicted_memory:.0f}% "
                    f"lat={plan.predicted_latency_ms:.1f}ms"
                )
            )
        parts.extend(
            [
                Text(""),
                Text(f"Cluster health  {self.result.cluster_health:.0f}"),
                Text(f"Confidence      {self.result.confidence:.0f}%"),
                Text(""),
                Text("View", style="dim"),
                Text("  Simulation  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _tradeoffs_view(self) -> RenderableType:
        assert self.result is not None
        parts: list[Text] = [
            Text("DISTRIBUTED SCHEDULER", style="bold bright_magenta"),
            Text(""),
            Text("Trade-offs", style="bold"),
            Text(""),
        ]
        if not self.result.trade_offs:
            parts.append(Text("  (none)", style="dim"))
        for t in self.result.trade_offs:
            parts.append(Text(f"  · vs {t.versus_node} (Δ {t.score_delta:.1f})"))
            parts.append(Text(f"    {t.summary}", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Trade-offs  (] cycles)"),
            ]
        )
        return Group(*parts)
