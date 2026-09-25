"""Rich formatter for the Autonomous Research Lab (dashboard shortcut B)."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.research_ai.models import (
    Discovery,
    Experiment,
    JournalEntry,
    ResearchQuestion,
    Result,
)


@dataclass(frozen=True, slots=True)
class ResearchLabPanel:
    """Center-panel renderable for Autonomous Research Lab (shortcut B)."""

    questions: tuple[ResearchQuestion, ...] = ()
    experiments: tuple[Experiment, ...] = ()
    results: tuple[Result, ...] = ()
    verified: tuple[Discovery, ...] = ()
    rejected: tuple[Discovery, ...] = ()
    journal: tuple[JournalEntry, ...] = ()
    view: str = "discoveries"

    def __rich__(self) -> RenderableType:
        if (
            not self.questions
            and not self.experiments
            and not self.verified
            and not self.rejected
        ):
            return Panel(
                Text(
                    "AUTONOMOUS RESEARCH idle.\n"
                    "Generates twin experiments from verified evidence only.\n"
                    "Never executes shell commands · never touches live telemetry.\n"
                    "B opens this page · R remains Graph Reasoning.\n"
                    "Status: Digital Twin research only",
                    style="dim",
                ),
                title="Research Lab",
                border_style="bright_yellow",
            )

        view = self.view.lower()
        if view == "questions":
            body = self._questions_view()
        elif view == "experiments":
            body = self._experiments_view()
        elif view == "rejected":
            body = self._rejected_view()
        elif view == "journal":
            body = self._journal_view()
        else:
            body = self._discoveries_view()

        return Panel(body, title="Research Lab", border_style="bright_yellow")

    def _discoveries_view(self) -> RenderableType:
        top = self.verified[0] if self.verified else None
        question = self.questions[0] if self.questions else None
        result = self.results[0] if self.results else None
        experiment = self.experiments[0] if self.experiments else None
        parts: list[Text] = [
            Text("AUTONOMOUS RESEARCH", style="bold bright_yellow"),
            Text(""),
            Text("Question", style="bold"),
            Text(f"  {question.title if question else (top.title if top else '—')}"),
            Text(""),
            Text("Experiments", style="bold"),
            Text(f"  {experiment.iterations if experiment else len(self.experiments)}"),
            Text(""),
        ]
        if result is not None:
            parts.extend(
                [
                    Text("Successful", style="bold"),
                    Text(f"  {result.successful_iterations}"),
                    Text(""),
                    Text("Reproducibility", style="bold"),
                    Text(f"  {result.reproducibility:.0f}%"),
                    Text(""),
                ]
            )
        if top is not None:
            parts.extend(
                [
                    Text("Conclusion", style="bold"),
                    Text(f"  {top.summary}"),
                    Text(""),
                    Text("Confidence", style="bold"),
                    Text(f"  {top.confidence:.0f}%"),
                    Text(""),
                    Text("Status", style="bold"),
                    Text("  Verified Discovery"),
                ]
            )
        else:
            parts.extend(
                [
                    Text("Status", style="bold"),
                    Text("  Awaiting verified discoveries"),
                ]
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Verified Discoveries  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _questions_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("AUTONOMOUS RESEARCH", style="bold bright_yellow"),
            Text(""),
            Text("Questions", style="bold"),
            Text(""),
        ]
        if not self.questions:
            parts.append(Text("  (none)", style="dim"))
        for q in self.questions[:10]:
            parts.append(Text(f"  · {q.title}"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Questions  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _experiments_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("AUTONOMOUS RESEARCH", style="bold bright_yellow"),
            Text(""),
            Text("Active Experiments", style="bold"),
            Text(""),
        ]
        if not self.experiments:
            parts.append(Text("  (none)", style="dim"))
        for exp in self.experiments[:10]:
            parts.append(
                Text(f"  · {exp.id[:16]}…  {exp.scenario}  " f"iters={exp.iterations}")
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Active Experiments  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _rejected_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("AUTONOMOUS RESEARCH", style="bold bright_yellow"),
            Text(""),
            Text("Rejected Hypotheses", style="bold"),
            Text(""),
        ]
        if not self.rejected:
            parts.append(Text("  (none)", style="dim"))
        for d in self.rejected[:10]:
            parts.append(Text(f"  · {d.title[:70]}"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Rejected Hypotheses  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _journal_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("AUTONOMOUS RESEARCH", style="bold bright_yellow"),
            Text(""),
            Text("Research Journal", style="bold"),
            Text(""),
        ]
        if not self.journal:
            parts.append(Text("  (empty)", style="dim"))
        for entry in self.journal[-12:]:
            stamp = entry.timestamp.strftime("%H:%M:%S")
            parts.append(
                Text(
                    f"  {stamp}  {entry.outcome}  "
                    f"repro={entry.reproducibility:.0f}%  "
                    f"exp={entry.experiment_id[:10]}"
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Research Journal  (] cycles)"),
            ]
        )
        return Group(*parts)
