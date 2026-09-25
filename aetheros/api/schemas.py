"""Pydantic response models for major read-only API routes.

Structured contracts replace ad-hoc ``dict[str, Any]`` on high-traffic
endpoints. Simulation-only / human-controlled semantics unchanged.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Liveness probe payload."""

    status: str
    version: str
    mode: str
    control: str


class PipelineStageOut(BaseModel):
    """One Infinity pipeline stage."""

    stage_id: str
    name: str
    package: str
    description: str
    produces: str


class GenerationOut(BaseModel):
    """One platform generation catalog entry."""

    version: str
    codename: str
    package: str
    summary: str
    principles: list[str]


class LayerStatusOut(BaseModel):
    """One Infinity layer readiness line."""

    name: str
    ready: bool
    detail: str


class InfinityOverview(BaseModel):
    """GET /infinity response."""

    identity: str
    status: str
    generation_count: int
    layers_ready: int
    principles: list[str]
    pipeline: list[PipelineStageOut]
    generations: list[GenerationOut]
    layers: list[LayerStatusOut]


class FabricOverview(BaseModel):
    """GET /fabric response."""

    connected_nodes: int
    regions: int
    datacenters: int
    clusters: int
    synchronization: float
    global_health: float
    status: str
    sample_graph_nodes: int
    sample_graph_edges: int


class ResilienceOut(BaseModel):
    """Nested resilience scores on Sentinel overview."""

    health: float
    stability: float
    redundancy: float
    risk: str
    explanation: str


class SentinelOverview(BaseModel):
    """GET /sentinel response."""

    health: float
    risk: str
    active_anomalies: int
    predicted_cascade: str
    recommended_strategy: str
    confidence: float
    status: str
    resilience: ResilienceOut


class AnomalyOut(BaseModel):
    """One Sentinel anomaly row."""

    id: str
    kind: str
    severity: str
    title: str
    description: str
    metric: str
    value: float = Field(description="Observed metric value for the anomaly.")
