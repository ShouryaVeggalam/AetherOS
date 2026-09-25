"""Aether Observatory — attention heatmap and cognition views (server-side).

Next.js UI lives under ``observatory/web``. This module provides deterministic
render data for Attention Map and cognition replay.
"""

from __future__ import annotations

from dataclasses import dataclass

from labs.aether.models.types import AttentionAllocation, CognitionPlan


@dataclass(frozen=True, slots=True)
class AttentionHeatmapCell:
    """One channel cell for the Attention Map."""

    channel: str
    weight: float
    intensity: float  # 0–1 normalized for UI heat


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
