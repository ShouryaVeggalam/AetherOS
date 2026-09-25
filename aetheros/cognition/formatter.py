"""Rich formatter for v3 Cognition Core state."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.cognition.models import CognitionState


@dataclass(frozen=True, slots=True)
class CognitionCorePanel:
    """Center-panel renderable for CognitionState (read-only)."""

    state: CognitionState | None

    def __rich__(self) -> RenderableType:
        """Render context, hypotheses, verified explanations, plans, confidence."""

        if self.state is None:
            return Panel(
                Text(
                    "COGNITION CORE idle.\n"
                    "Call CognitionEngine.observe/reason/verify/plan.\n"
                    "Deterministic evidence reasoning — not an LLM.\n"
                    "Status: Read-only",
                    style="dim",
                ),
                title="Cognition Core",
                border_style="bright_white",
            )
        state = self.state
        top = state.verified_explanations[0] if state.verified_explanations else None
        plan = state.plans[0] if state.plans else None
        parts: list[Text] = [
            Text("COGNITION CORE", style="bold"),
            Text(""),
            Text("Context", style="bold"),
            Text(f"  {state.context}"),
            Text(""),
            Text("Evidence", style="bold"),
            Text(f"  {len(state.evidence)}"),
            Text(""),
            Text("Active Hypotheses", style="bold"),
            Text(f"  {len(state.active_hypotheses)}"),
            Text(""),
            Text("Verified Explanations", style="bold"),
            Text(f"  {len(state.verified_explanations)}"),
            Text(""),
        ]
        if top is not None:
            parts.extend(
                [
                    Text("Top Verified", style="bold"),
                    Text(f"  {top.hypothesis.title}"),
                    Text(f"  confidence {top.confidence:.0f}%", style="dim"),
                    Text(""),
                ]
            )
        if plan is not None:
            parts.extend(
                [
                    Text("Top Plan", style="bold"),
                    Text(f"  {plan.title}"),
                    Text(f"  {plan.summary}", style="dim"),
                    Text(""),
                ]
            )
        parts.extend(
            [
                Text("Confidence", style="bold"),
                Text(f"  {state.confidence:.0f}%"),
                Text(""),
                Text(
                    "Status  Research-grade · simulation-backed plans only", style="dim"
                ),
            ]
        )
        return Panel(Group(*parts), title="Cognition Core", border_style="bright_white")
