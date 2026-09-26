"""Rich formatter for Policy Studio dashboard panel (shortcut P).

# remains Predictive. P opens Policy Studio views.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.policy.models import EvaluationResult, Policy, SimulationImpact
from aetheros.policy.parser import rule_to_expression


@dataclass(frozen=True, slots=True)
class PolicyStudioPanel:
    """Center-panel renderable for Policy Studio (shortcut P)."""

    policies: tuple[Policy, ...] = ()
    results: tuple[EvaluationResult, ...] = ()
    impact: SimulationImpact | None = None
    selected: Policy | None = None
    view: str = "active"

    def __rich__(self) -> RenderableType:
        if not self.policies and not self.results:
            return Panel(
                Text(
                    "POLICY STUDIO idle.\n"
                    "Define governance rules for recommendations & simulations.\n"
                    "Never controls the OS · no shell · no remote execution.\n"
                    "P opens this page · # remains Predictive.\n"
                    "Status: Read-only / Simulation",
                    style="dim",
                ),
                title="Policy Studio",
                border_style="bright_blue",
            )

        view = self.view.lower()
        if view in {"versions", "version"}:
            body = self._versions_view()
        elif view in {"builder", "rule", "rule builder"}:
            body = self._builder_view()
        elif view in {"evaluation", "evaluate"}:
            body = self._evaluation_view()
        elif view in {"simulation", "impact", "simulation impact"}:
            body = self._simulation_view()
        else:
            body = self._active_view()
        return Panel(body, title="Policy Studio", border_style="bright_blue")

    def _active_view(self) -> RenderableType:
        matched = tuple(r for r in self.results if r.matched)
        top = self.selected
        if top is None and matched:
            top = max(matched, key=lambda r: r.policy.priority).policy
        if top is None and self.policies:
            top = max(self.policies, key=lambda p: p.priority)
        parts: list[Text] = [
            Text("POLICY STUDIO", style="bold bright_blue"),
            Text(""),
            Text("Active Policies", style="bold"),
            Text(
                f"  {sum(1 for p in self.policies if p.enabled and p.status == 'published')}"
            ),
            Text(""),
            Text("Matched", style="bold"),
            Text(f"  {len(matched)}"),
            Text(""),
        ]
        if top is not None:
            rule = top.rules[0] if top.rules else None
            parts.extend(
                [
                    Text("Highest Priority", style="bold"),
                    Text(f"  {top.name}"),
                    Text(""),
                    Text("Rule", style="bold"),
                    Text(f"  {rule_to_expression(rule) if rule else '—'}"),
                    Text(""),
                    Text("Action", style="bold"),
                    Text(f"  {rule.action if rule else '—'}"),
                    Text(""),
                    Text("Status", style="bold"),
                    Text("  Applied (Simulation)"),
                ]
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Active Policies  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _versions_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("POLICY STUDIO", style="bold bright_blue"),
            Text(""),
            Text("Versions", style="bold"),
            Text(""),
        ]
        if not self.policies:
            parts.append(Text("  (none)", style="dim"))
        for policy in self.policies:
            flag = "on" if policy.enabled else "off"
            parts.append(
                Text(
                    f"  · {policy.id:<22} v{policy.version}  "
                    f"[{policy.status}/{flag}]  prio={policy.priority}"
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Versions  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _builder_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("POLICY STUDIO", style="bold bright_blue"),
            Text(""),
            Text("Rule Builder", style="bold"),
            Text(""),
            Text("  Operators", style="bold"),
            Text("  ==  !=  >  <  >=  <=  IN  NOT_IN"),
            Text(""),
            Text("  Examples", style="bold"),
            Text("  battery < 20"),
            Text("  intent == CODING"),
            Text('  region IN ["Hyderabad"]'),
            Text(""),
            Text("  Actions are advisory only (never OS execution).", style="dim"),
            Text(""),
            Text("View", style="dim"),
            Text("  Rule Builder  (] cycles)"),
        ]
        return Group(*parts)

    def _evaluation_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("POLICY STUDIO", style="bold bright_blue"),
            Text(""),
            Text("Evaluation", style="bold"),
            Text(""),
        ]
        matched = [r for r in self.results if r.matched]
        if not matched:
            parts.append(Text("  (no matches)", style="dim"))
        for result in matched:
            parts.append(
                Text(
                    f"  · {result.policy.name:<24} "
                    f"conf={result.confidence:.2f}  → {result.action or '—'}"
                )
            )
            parts.append(Text(f"      {result.explanation}", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Evaluation  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _simulation_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("POLICY STUDIO", style="bold bright_blue"),
            Text(""),
            Text("Simulation Impact", style="bold"),
            Text(""),
        ]
        if self.impact is None:
            parts.append(Text("  (no simulation)", style="dim"))
        else:
            parts.append(
                Text(
                    f"  Matched policies: {sum(1 for r in self.impact.matched if r.matched)}"
                )
            )
            parts.append(Text(""))
            parts.append(Text("  Constraints", style="bold"))
            if not self.impact.constraints:
                parts.append(Text("    (none)", style="dim"))
            for item in self.impact.constraints:
                parts.append(Text(f"    · {item}"))
            parts.append(Text(""))
            parts.append(Text("  Filtered recommendations", style="bold"))
            if not self.impact.filtered_recommendations:
                parts.append(Text("    (none remain / none provided)", style="dim"))
            for title in self.impact.filtered_recommendations:
                parts.append(Text(f"    · {title}"))
            parts.append(Text(""))
            parts.append(Text("  Status", style="bold"))
            parts.append(Text("    Applied (Simulation)"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Simulation Impact  (] cycles)"),
            ]
        )
        return Group(*parts)
