"""Resource Graph Rich panel — Tree view of host resources.

Presentation only. Builds trees from an immutable ResourceGraph.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree

from aetheros.graph.models import ResourceGraph, ResourceNode
from aetheros.graph.queries import edges_from, nodes_of_type


@dataclass(frozen=True, slots=True)
class ResourceGraphPanel:
    """Center-panel renderable for the Resource Graph Engine."""

    graph: ResourceGraph | None

    def __rich__(self) -> RenderableType:
        """Render a Rich Tree of system resources."""

        if self.graph is None:
            return Panel(
                Text(
                    "Resource Graph idle.\n"
                    "Press Y after telemetry is flowing.\n"
                    "G remains Genesis — Y opens the host resource graph.",
                    style="dim",
                ),
                title="Resource Graph",
                border_style="bright_green",
            )
        graph = self.graph
        root = Tree(Text("System", style="bold bright_green"))
        _add_cpu_branch(root, graph)
        _add_simple_branch(root, graph, "Memory", "memory")
        for disk in nodes_of_type(graph, "Disk"):
            root.add(Text(disk.name, style="cyan"))
        battery = graph.get_node("battery")
        if battery is not None:
            root.add(Text(f"Battery ({_meta(battery, 'percent')}%)", style="yellow"))
        intent = graph.get_node("intent:active")
        if intent is not None:
            root.add(Text(f"Intent: {intent.name}", style="magenta"))
        for process in nodes_of_type(graph, "Process"):
            branch = root.add(Text(process.name, style="bold"))
            for edge in edges_from(graph, process.id):
                target = graph.get_node(edge.target)
                label = target.name if target is not None else edge.target
                branch.add(
                    Text(
                        f"{edge.relationship.title().replace('_', ' ')} {label}",
                        style="dim",
                    )
                )
        body = Group(
            Text("RESOURCE GRAPH ENGINE", style="bold bright_green"),
            Text(
                f"nodes {len(graph.nodes)} · edges {len(graph.edges)} · "
                f"schema {graph.schema_version}",
                style="dim",
            ),
            Text(""),
            root,
            Text(""),
            Text("Y/ESC leave  ·  immutable  ·  telemetry-backed", style="dim"),
        )
        return Panel(body, title="Resource Graph", border_style="bright_green")


def _add_cpu_branch(root: Tree, graph: ResourceGraph) -> None:
    """Attach CPU and core children."""

    cpu = graph.get_node("cpu")
    if cpu is None:
        return
    branch = root.add(
        Text(f"CPU ({_meta(cpu, 'percent')}%)", style="bold cyan")
    )
    for edge in edges_from(graph, "cpu"):
        if edge.relationship != "ALLOCATES":
            continue
        core = graph.get_node(edge.target)
        if core is not None and core.id.startswith("cpu:core:"):
            branch.add(Text(f"{core.name} ({_meta(core, 'percent')}%)"))


def _add_simple_branch(root: Tree, graph: ResourceGraph, title: str, node_id: str) -> None:
    """Attach a single named resource node."""

    node = graph.get_node(node_id)
    if node is None:
        return
    root.add(Text(f"{title} ({_meta(node, 'percent')}%)", style="cyan"))


def _meta(node: ResourceNode, key: str) -> str:
    """Read one metadata value or em-dash."""

    for meta_key, value in node.metadata:
        if meta_key == key:
            return value
    return "—"
