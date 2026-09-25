"""Rich formatter for the Causal Knowledge Graph (dashboard shortcut N)."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from aetheros.knowledge.models import CausalKnowledgeGraph, KnowledgeNode
from aetheros.knowledge.traversal import find_effects, shortest_causal_path


@dataclass(frozen=True, slots=True)
class CausalKnowledgePanel:
    """Center-panel renderable for Causal Knowledge Graph (shortcut N)."""

    graph: CausalKnowledgeGraph | None = None
    view: str = "causal"
    focus_path: tuple[KnowledgeNode, ...] = ()

    def __rich__(self) -> RenderableType:
        if self.graph is None or (not self.graph.nodes and not self.graph.edges):
            return Panel(
                Text(
                    "CAUSAL KNOWLEDGE GRAPH idle.\n"
                    "Build from Resource Graph + Operational Memory +\n"
                    "Research / Reasoning / Twin evidence only.\n"
                    "No fabricated relationships.\n"
                    "N opens this page · K remains Cognitive Graph.\n"
                    "Status: Verified knowledge only",
                    style="dim",
                ),
                title="Causal Knowledge Graph",
                border_style="bright_cyan",
            )

        view = self.view.lower()
        if view == "ontology":
            body = self._ontology_view()
        elif view == "discoveries":
            body = self._discoveries_view()
        elif view == "relationships":
            body = self._relationships_view()
        elif view == "evidence":
            body = self._evidence_view()
        else:
            body = self._causal_view()

        return Panel(
            body,
            title="Causal Knowledge Graph",
            border_style="bright_cyan",
        )

    def _causal_view(self) -> RenderableType:
        assert self.graph is not None
        path = self.focus_path or self._default_path()
        parts: list[Text | Tree] = [
            Text("CAUSAL KNOWLEDGE GRAPH", style="bold bright_cyan"),
            Text(""),
        ]
        if path:
            tree = Tree(Text(path[0].name, style="bold"))
            cursor = tree
            for node in path[1:]:
                cursor = cursor.add(Text(node.name))
            parts.append(tree)
            evidence = sum(
                e.evidence_count
                for e in self.graph.edges
                if e.source in {n.id for n in path} or e.target in {n.id for n in path}
            )
            confidences = [
                e.confidence
                for e in self.graph.edges
                if e.source in {n.id for n in path} and e.target in {n.id for n in path}
            ]
            confidence = max(confidences) if confidences else 0.0
            parts.extend(
                [
                    Text(""),
                    Text("Supported by", style="bold"),
                    Text(f"  {max(evidence, 1)} verified observations"),
                    Text(""),
                    Text("Confidence", style="bold"),
                    Text(f"  {confidence:.0f}%"),
                ]
            )
        else:
            parts.append(Text("  (no causal chain)", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Causal Graph  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _ontology_view(self) -> RenderableType:
        assert self.graph is not None
        parts: list[Text] = [
            Text("CAUSAL KNOWLEDGE GRAPH", style="bold bright_cyan"),
            Text(""),
            Text("Ontology", style="bold"),
            Text(""),
        ]
        counts: dict[str, int] = {}
        for node in self.graph.nodes:
            counts[node.type] = counts.get(node.type, 0) + 1
        for ntype in sorted(counts):
            parts.append(Text(f"  {ntype}: {counts[ntype]}"))
        parts.extend(
            [
                Text(""),
                Text(f"Nodes  {len(self.graph.nodes)}"),
                Text(f"Edges  {len(self.graph.edges)}"),
                Text(""),
                Text("View", style="dim"),
                Text("  Ontology  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _discoveries_view(self) -> RenderableType:
        assert self.graph is not None
        parts: list[Text] = [
            Text("CAUSAL KNOWLEDGE GRAPH", style="bold bright_cyan"),
            Text(""),
            Text("Discoveries", style="bold"),
            Text(""),
        ]
        discoveries = [n for n in self.graph.nodes if n.type == "Discovery"]
        if not discoveries:
            parts.append(Text("  (none)", style="dim"))
        for node in discoveries[:12]:
            parts.append(Text(f"  · {node.name}"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Discoveries  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _relationships_view(self) -> RenderableType:
        assert self.graph is not None
        parts: list[Text] = [
            Text("CAUSAL KNOWLEDGE GRAPH", style="bold bright_cyan"),
            Text(""),
            Text("Relationships", style="bold"),
            Text(""),
        ]
        if not self.graph.edges:
            parts.append(Text("  (none)", style="dim"))
        for edge in self.graph.edges[:16]:
            src = self.graph.get_node(edge.source)
            dst = self.graph.get_node(edge.target)
            sname = src.name if src else edge.source
            dname = dst.name if dst else edge.target
            parts.append(
                Text(
                    f"  {sname} -[{edge.relationship}]-> {dname}  "
                    f"({edge.confidence:.0f}% · {edge.evidence_count} ev)"
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Relationships  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _evidence_view(self) -> RenderableType:
        assert self.graph is not None
        parts: list[Text] = [
            Text("CAUSAL KNOWLEDGE GRAPH", style="bold bright_cyan"),
            Text(""),
            Text("Evidence", style="bold"),
            Text(""),
        ]
        total = sum(e.evidence_count for e in self.graph.edges)
        parts.append(Text(f"  Total evidence units: {total}"))
        parts.append(Text(f"  Verified edges: {len(self.graph.edges)}"))
        top = sorted(self.graph.edges, key=lambda e: (-e.evidence_count, -e.confidence))
        for edge in top[:8]:
            parts.append(
                Text(
                    f"  · {edge.source}->{edge.target} "
                    f"{edge.relationship} n={edge.evidence_count}"
                )
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Evidence  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _default_path(self) -> tuple[KnowledgeNode, ...]:
        assert self.graph is not None
        # Prefer Intent → … → resource chain from seeds.
        intents = [n for n in self.graph.nodes if n.type == "Intent"]
        memories = [n for n in self.graph.nodes if n.type == "Pattern"]
        cpu = self.graph.get_node("cpu")
        memory = self.graph.get_node("memory")
        disk = self.graph.get_node("disk")
        if intents and cpu is not None:
            path = shortest_causal_path(self.graph, intents[0].id, cpu.id)
            if path:
                # Extend with effects if present.
                chain = list(path)
                if memory is not None and memory not in chain:
                    effects = find_effects(self.graph, cpu.id)
                    if any(e.id == "memory" for e in effects):
                        chain.append(memory)
                if disk is not None and memory is not None and disk not in chain:
                    effects = find_effects(self.graph, memory.id)
                    if any(e.id == "disk" for e in effects):
                        chain.append(disk)
                return tuple(chain)
        if memories and cpu is not None:
            path = shortest_causal_path(self.graph, memories[0].id, cpu.id)
            if path:
                return path
        if self.graph.nodes:
            return (self.graph.nodes[0],)
        return ()
