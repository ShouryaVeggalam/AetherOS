"""Rich formatter for Global Knowledge Graph (dashboard shortcut K).

^ remains Cognitive Graph. K opens Global Knowledge Graph views.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.global_graph.evidence import EvidenceIndex
from aetheros.global_graph.models import GlobalKnowledgeGraph
from aetheros.global_graph.validator import ValidationReport


@dataclass(frozen=True, slots=True)
class GlobalKnowledgePanel:
    """Center-panel renderable for Global Knowledge Graph (shortcut K)."""

    graph: GlobalKnowledgeGraph | None = None
    evidence: EvidenceIndex | None = None
    validation: ValidationReport | None = None
    view: str = "world"

    def __rich__(self) -> RenderableType:
        if self.graph is None:
            return Panel(
                Text(
                    "GLOBAL KNOWLEDGE GRAPH idle.\n"
                    "Federation · Topology · Memory · Twin · Consensus · Research.\n"
                    "Verified relationships only — never fabricated.\n"
                    "K opens this page · ^ remains Cognitive Graph.\n"
                    "Status: Verified Graph",
                    style="dim",
                ),
                title="Global Knowledge Graph",
                border_style="bright_yellow",
            )

        view = self.view.lower()
        if view == "regions":
            body = self._regions_view()
        elif view == "clusters":
            body = self._clusters_view()
        elif view == "knowledge":
            body = self._knowledge_view()
        elif view == "discoveries":
            body = self._discoveries_view()
        elif view == "evidence":
            body = self._evidence_view()
        else:
            body = self._world_view()
        return Panel(body, title="Global Knowledge Graph", border_style="bright_yellow")

    def _top_discovery(self) -> str:
        assert self.graph is not None
        discoveries = self.graph.nodes_of_type("Discovery")
        if not discoveries:
            return "—"
        return discoveries[0].name

    def _mean_confidence(self) -> float:
        assert self.graph is not None
        if not self.graph.edges:
            return 0.0
        return sum(e.confidence for e in self.graph.edges) / len(self.graph.edges)

    def _world_view(self) -> RenderableType:
        assert self.graph is not None
        regions = len(self.graph.nodes_of_type("Region"))
        clusters = len(self.graph.nodes_of_type("Cluster"))
        nodes = len(self.graph.nodes_of_type("Node"))
        rels = len(self.graph.edges)
        status = "Verified Graph"
        if self.validation is not None and not self.validation.ok:
            status = f"Invalid ({self.validation.error_count} errors)"
        parts: list[Text] = [
            Text("GLOBAL KNOWLEDGE GRAPH", style="bold bright_yellow"),
            Text(""),
            Text("Regions", style="bold"),
            Text(f"  {regions}"),
            Text(""),
            Text("Clusters", style="bold"),
            Text(f"  {clusters}"),
            Text(""),
            Text("Nodes", style="bold"),
            Text(f"  {nodes}"),
            Text(""),
            Text("Verified Relationships", style="bold"),
            Text(f"  {rels:,}"),
            Text(""),
            Text("Top Discovery", style="bold"),
            Text(f"  {self._top_discovery()}"),
            Text(""),
            Text("Confidence", style="bold"),
            Text(f"  {self._mean_confidence():.0f}%"),
            Text(""),
            Text("Status", style="bold"),
            Text(f"  {status}"),
            Text(""),
            Text("View", style="dim"),
            Text("  World Graph  (] cycles)"),
        ]
        return Group(*parts)

    def _regions_view(self) -> RenderableType:
        assert self.graph is not None
        parts: list[Text] = [
            Text("GLOBAL KNOWLEDGE GRAPH", style="bold bright_yellow"),
            Text(""),
            Text("Regions", style="bold"),
        ]
        for node in self.graph.nodes_of_type("Region"):
            parts.append(Text(f"  • {node.name}"))
        parts.extend(
            [
                Text(""),
                Text("Status", style="bold"),
                Text("  Verified Graph"),
                Text(""),
                Text("View", style="dim"),
                Text("  Regions  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _clusters_view(self) -> RenderableType:
        assert self.graph is not None
        parts: list[Text] = [
            Text("GLOBAL KNOWLEDGE GRAPH", style="bold bright_yellow"),
            Text(""),
            Text("Clusters", style="bold"),
        ]
        for node in self.graph.nodes_of_type("Cluster"):
            parts.append(Text(f"  • {node.name}"))
        parts.extend(
            [
                Text(""),
                Text("Status", style="bold"),
                Text("  Verified Graph"),
                Text(""),
                Text("View", style="dim"),
                Text("  Clusters  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _knowledge_view(self) -> RenderableType:
        assert self.graph is not None
        intel = (
            list(self.graph.nodes_of_type("Context"))
            + list(self.graph.nodes_of_type("Intent"))
            + list(self.graph.nodes_of_type("Pattern"))
            + list(self.graph.nodes_of_type("Simulation"))
            + list(self.graph.nodes_of_type("Consensus"))
            + list(self.graph.nodes_of_type("Research"))
        )
        parts: list[Text] = [
            Text("GLOBAL KNOWLEDGE GRAPH", style="bold bright_yellow"),
            Text(""),
            Text("Knowledge", style="bold"),
        ]
        for node in intel[:12]:
            parts.append(Text(f"  [{node.type}] {node.name}"))
        parts.extend(
            [
                Text(""),
                Text("Status", style="bold"),
                Text("  Verified Graph"),
                Text(""),
                Text("View", style="dim"),
                Text("  Knowledge  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _discoveries_view(self) -> RenderableType:
        assert self.graph is not None
        parts: list[Text] = [
            Text("GLOBAL KNOWLEDGE GRAPH", style="bold bright_yellow"),
            Text(""),
            Text("Discoveries", style="bold"),
        ]
        for node in self.graph.nodes_of_type("Discovery"):
            parts.append(Text(f"  • {node.name}"))
        if not self.graph.nodes_of_type("Discovery"):
            parts.append(Text("  (none)", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("Status", style="bold"),
                Text("  Verified Graph"),
                Text(""),
                Text("View", style="dim"),
                Text("  Discoveries  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _evidence_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("GLOBAL KNOWLEDGE GRAPH", style="bold bright_yellow"),
            Text(""),
            Text("Evidence", style="bold"),
        ]
        records = self.evidence.records if self.evidence else ()
        for record in records[:10]:
            parts.append(Text(f"  [{record.kind}] {record.summary[:64]}"))
            parts.append(Text(f"    ref={record.source_ref}", style="dim"))
        if not records:
            parts.append(Text("  (none)", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("Status", style="bold"),
                Text("  Verified Graph"),
                Text(""),
                Text("View", style="dim"),
                Text("  Evidence  (] cycles)"),
            ]
        )
        return Group(*parts)
