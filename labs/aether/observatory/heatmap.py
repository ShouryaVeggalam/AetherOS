"""Aether Observatory — attention heatmap, task DAG, reflection timeline."""

from __future__ import annotations

from dataclasses import dataclass

from labs.aether.decomposition.engine import topological_order
from labs.aether.models.types import (
    AttentionAllocation,
    CognitionPlan,
    Critique,
    Reflection,
    TaskGraph,
)


@dataclass(frozen=True, slots=True)
class AttentionHeatmapCell:
    """One channel cell for the Attention Map."""

    channel: str
    weight: float
    intensity: float


@dataclass(frozen=True, slots=True)
class AttentionMapView:
    """Observatory Attention Map payload."""

    allocation_id: str
    goal_id: str
    cells: tuple[AttentionHeatmapCell, ...]
    reasoning_budget: float
    retrieval_budget: float
    confidence: float
    factors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CognitionReplayFrame:
    """One frame in a cognition replay timeline."""

    stage: str
    attention_share: float
    description: str


@dataclass(frozen=True, slots=True)
class TaskGraphView:
    """Observatory Task Graph payload."""

    graph_id: str
    objective: str
    node_count: int
    edge_count: int
    topo_order: tuple[str, ...]
    levels: tuple[tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class ReflectionTimelineEntry:
    """One reflection event for the timeline."""

    reflection_id: str
    plan_id: str
    weakness_count: int
    assumption_count: int
    improvement_count: int
    summary: str


def build_attention_map(allocation: AttentionAllocation) -> AttentionMapView:
    """Build an Attention Map from an allocation (deterministic)."""

    weights = allocation.weights
    max_w = max(float(v) for v in weights.values()) or 1.0
    cells = tuple(
        AttentionHeatmapCell(
            channel=channel,
            weight=round(float(weights[channel]), 6),
            intensity=round(float(weights[channel]) / max_w, 4),
        )
        for channel in ("focus", "memory", "exploration", "verification")
        if channel in weights
    )
    return AttentionMapView(
        allocation_id=allocation.id,
        goal_id=allocation.goal_id,
        cells=cells,
        reasoning_budget=allocation.reasoning_budget,
        retrieval_budget=allocation.retrieval_budget,
        confidence=allocation.confidence,
        factors=allocation.factors,
    )


def build_replay(plan: CognitionPlan) -> tuple[CognitionReplayFrame, ...]:
    """Build cognition replay frames from plan stages."""

    return tuple(
        CognitionReplayFrame(
            stage=s.name,
            attention_share=s.attention_share,
            description=s.description,
        )
        for s in plan.stages
    )


def build_task_graph_view(graph: TaskGraph) -> TaskGraphView:
    """Summarize a DAG for Observatory Task Graph page."""

    order = tuple(t.id for t in topological_order(graph))
    edges = sum(len(t.dependencies) for t in graph.tasks)
    levels: dict[str, int] = {}
    for task in graph.tasks:
        levels[task.type] = levels.get(task.type, 0) + 1
    return TaskGraphView(
        graph_id=graph.id,
        objective=graph.objective,
        node_count=len(graph.tasks),
        edge_count=edges,
        topo_order=order,
        levels=tuple(sorted(levels.items())),
    )


def build_reflection_timeline(
    reflections: tuple[Reflection, ...],
) -> tuple[ReflectionTimelineEntry, ...]:
    return tuple(
        ReflectionTimelineEntry(
            reflection_id=r.id,
            plan_id=r.plan_id,
            weakness_count=len(r.weaknesses),
            assumption_count=len(r.assumptions),
            improvement_count=len(r.improvements),
            summary=r.reasoning_summary[:120],
        )
        for r in reflections
    )


def render_attention_ascii(view: AttentionMapView, *, width: int = 24) -> str:
    """ASCII heatmap for terminals / tests."""

    lines = [
        f"ATTENTION MAP  id={view.allocation_id}",
        f"goal={view.goal_id}  conf={view.confidence:.0%}  "
        f"reason={view.reasoning_budget:.2f}  retrieve={view.retrieval_budget:.2f}",
        "",
    ]
    for cell in view.cells:
        bar_len = max(1, int(round(cell.intensity * width)))
        bar = "█" * bar_len + "░" * (width - bar_len)
        lines.append(f"  {cell.channel:<12} {bar} {cell.weight:.2f}")
    return "\n".join(lines)


def render_task_graph_ascii(view: TaskGraphView) -> str:
    lines = [
        f"TASK GRAPH  id={view.graph_id}",
        f"objective={view.objective}",
        f"nodes={view.node_count}  edges={view.edge_count}",
        "",
        "Levels:",
    ]
    for level, count in view.levels:
        lines.append(f"  {level:<12} {count}")
    lines.append("")
    lines.append("Topo: " + " → ".join(view.topo_order[:8]))
    if len(view.topo_order) > 8:
        lines.append(f"  … +{len(view.topo_order) - 8} more")
    return "\n".join(lines)


def render_critique_ascii(critique: Critique) -> str:
    lines = [
        f"CRITIQUE  id={critique.id}  plan={critique.plan_id}",
        f"overall={critique.overall:.0%}  verdict={critique.verdict}",
        "",
    ]
    for score in critique.scores:
        bar = "█" * int(score.score * 20) + "░" * (20 - int(score.score * 20))
        lines.append(f"  {score.criterion:<24} {bar} {score.score:.2f}")
    return "\n".join(lines)
