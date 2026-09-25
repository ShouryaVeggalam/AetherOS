"""Rich formatter for Graph Reasoning Engine panels.

Presentation only. Never generates hypotheses or mutates graphs.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from aetheros.reasoning.models import Observation, ReasoningPath, VerifiedExplanation


@dataclass(frozen=True, slots=True)
class GraphReasoningPanel:
    """Center-panel renderable for graph reasoning results."""

    explanation: VerifiedExplanation | None
    observation: Observation | None = None

    def __rich__(self) -> RenderableType:
        """Render observation, verified cause, path tree, confidence, evidence."""

        if self.explanation is None:
            obs = self.observation
            detail = (
                f"Observation queued: {obs.title} ({obs.metric}={obs.value:.1f})"
                if obs is not None
                else "No verified graph explanation yet."
            )
            return Panel(
                Text(
                    "GRAPH REASONING idle.\n"
                    f"{detail}\n"
                    "Press R after telemetry is flowing.\n"
                    "Explanations require real ResourceGraph paths.",
                    style="dim",
                ),
                title="Graph Reasoning",
                border_style="bright_cyan",
            )
        expl = self.explanation
        obs = expl.observation
        path_tree = _path_tree(expl.reasoning_paths)
        evidence_lines = Text()
        sources = sorted({item.source for item in expl.evidence})
        evidence_lines.append("Evidence\n", style="bold")
        for source in sources:
            evidence_lines.append(f"  • {source}\n", style="dim")
        if not sources:
            evidence_lines.append("  • (none)\n", style="dim")
        body = Group(
            Text("GRAPH REASONING", style="bold bright_cyan"),
            Text(""),
            Text("Observation", style="bold"),
            Text(f"  {obs.title}  ({obs.metric}={obs.value:.1f})"),
            Text(""),
            Text("Verified Cause", style="bold"),
            Text(f"  {expl.summary}"),
            Text(""),
            Text("Reasoning Path", style="bold"),
            path_tree,
            Text(""),
            Text("Confidence", style="bold"),
            Text(f"  {expl.confidence}%"),
            Text(""),
            evidence_lines,
            Text("R/ESC leave  ·  graph-derived  ·  no fabricated links", style="dim"),
        )
        return Panel(body, title="Graph Reasoning", border_style="bright_cyan")


def _path_tree(paths: tuple[ReasoningPath, ...]) -> Tree:
    """Build a Rich Tree for the first supporting path."""

    root = Tree(Text("Causal Tree", style="bold"))
    if not paths:
        root.add(Text("(no paths)", style="dim"))
        return root
    primary = max(paths, key=lambda path: path.depth)
    branch = root
    for index, node in enumerate(primary.nodes):
        label = node.name
        if index > 0:
            relation = primary.edges[index - 1].relationship
            label = f"{relation} → {node.name}"
        branch = branch.add(Text(label))
    if len(paths) > 1:
        root.add(Text(f"+ {len(paths) - 1} alternate path(s)", style="dim"))
    return root
