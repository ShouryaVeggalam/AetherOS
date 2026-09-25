"""Aether Observatory surfaces."""

from __future__ import annotations

from labs.aether.observatory.heatmap import (
    AttentionHeatmapCell,
    AttentionMapView,
    CognitionReplayFrame,
    ReflectionTimelineEntry,
    TaskGraphView,
    build_attention_map,
    build_reflection_timeline,
    build_replay,
    build_task_graph_view,
    render_attention_ascii,
    render_critique_ascii,
    render_task_graph_ascii,
)

__all__ = [
    "AttentionHeatmapCell",
    "AttentionMapView",
    "CognitionReplayFrame",
    "ReflectionTimelineEntry",
    "TaskGraphView",
    "build_attention_map",
    "build_reflection_timeline",
    "build_replay",
    "build_task_graph_view",
    "render_attention_ascii",
    "render_critique_ascii",
    "render_task_graph_ascii",
]
