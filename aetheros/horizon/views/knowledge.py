"""Horizon Knowledge — Global Knowledge Graph as Rich Tree.

Consumes GlobalKnowledgeGraph + evidence. Verified relationships only.
"""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.horizon.snapshot import HorizonSnapshot
from aetheros.horizon.widgets.metric_grid import MetricGrid
from aetheros.horizon.widgets.stat_card import StatCard
from aetheros.horizon.widgets.tree import HorizonTree, TreeNodeSpec


def render_knowledge(snapshot: HorizonSnapshot) -> RenderableType:
    """Render Global Knowledge Graph presentation from snapshot fields."""

    graph = snapshot.knowledge_graph
    if graph is None:
        body = Text(
            "KNOWLEDGE GRAPH idle.\nNo GlobalKnowledgeGraph in snapshot.\n"
            "Verified relationships only.",
            style="dim",
        )
        return Panel(
            body, title="Horizon · Knowledge Graph", border_style="bright_yellow"
        )

    regions = tuple(graph.nodes_of_type("Region"))
    clusters = tuple(graph.nodes_of_type("Cluster"))
    discoveries = tuple(graph.nodes_of_type("Discovery"))
    edges = tuple(getattr(graph, "edges", ()) or ())
    evidence = snapshot.knowledge_evidence
    evidence_count = 0
    if evidence is not None:
        evidence_count = len(tuple(getattr(evidence, "records", ()) or ()))
        if evidence_count == 0:
            evidence_count = int(getattr(evidence, "count", 0) or 0)
            if evidence_count == 0 and hasattr(evidence, "__len__"):
                try:
                    evidence_count = len(evidence)  # type: ignore[arg-type]
                except TypeError:
                    evidence_count = 0

    mean_conf = 0.0
    if edges:
        mean_conf = sum(float(getattr(e, "confidence", 0.0)) for e in edges) / len(
            edges
        )

    region_children = tuple(
        TreeNodeSpec(
            label=str(getattr(r, "name", r)),
            children=tuple(
                TreeNodeSpec(label=str(getattr(c, "name", c)), style="dim")
                for c in clusters
                if _region_of(c) == str(getattr(r, "id", ""))
                or _region_of(c) == str(getattr(r, "name", ""))
            ),
        )
        for r in regions
    )
    discovery_children = tuple(
        TreeNodeSpec(
            label=f"{getattr(d, 'name', d)}",
            style="bright_magenta",
        )
        for d in discoveries[:8]
    )
    tree = HorizonTree(
        root_label="Global Knowledge",
        children=(
            TreeNodeSpec(label="Regions", children=region_children),
            TreeNodeSpec(label="Discoveries", children=discovery_children),
        ),
    )
    cards = MetricGrid(
        cards=(
            StatCard("Relationships", str(len(edges)), tone="bright_yellow"),
            StatCard("Discoveries", str(len(discoveries)), tone="bright_magenta"),
            StatCard("Evidence", str(evidence_count), tone="bright_white"),
            StatCard("Confidence", f"{mean_conf:.0f}%", tone="bright_green"),
        )
    )
    status = "Verified Graph"
    validation = snapshot.knowledge_validation
    if validation is not None and not bool(getattr(validation, "ok", True)):
        status = f"Invalid ({getattr(validation, 'error_count', '?')} errors)"

    body = Group(
        Text("GLOBAL KNOWLEDGE GRAPH", style="bold bright_yellow"),
        Text(status, style="dim"),
        Text(""),
        cards,
        Text(""),
        tree,
    )
    return Panel(body, title="Horizon · Knowledge Graph", border_style="bright_yellow")


def _region_of(node: object) -> str:
    props = getattr(node, "properties", None) or {}
    if isinstance(props, dict):
        return str(props.get("region") or props.get("region_id") or "")
    return str(getattr(node, "region", "") or "")
