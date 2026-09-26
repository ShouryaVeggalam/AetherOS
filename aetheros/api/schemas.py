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


# --- Public API v1 (P2) ------------------------------------------------------


class V1HealthResponse(BaseModel):
    """GET /api/v1/health."""

    status: str
    version: str
    api_version: str = "v1"
    mode: str = "read-only"
    control: str = "human"


class V1ContextResponse(BaseModel):
    """GET /api/v1/context."""

    intent: str
    labels: dict[str, str] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)
    source: str = "context-engine"


class V1GraphNode(BaseModel):
    """One graph node in the public API."""

    id: str
    name: str
    kind: str
    attributes: dict[str, str] = Field(default_factory=dict)


class V1GraphEdge(BaseModel):
    """One graph edge in the public API."""

    source: str
    target: str
    relation: str
    weight: float = 1.0


class V1GraphResponse(BaseModel):
    """GET /api/v1/graph."""

    nodes: list[V1GraphNode]
    edges: list[V1GraphEdge]
    node_count: int
    edge_count: int


class V1ReasoningResponse(BaseModel):
    """GET /api/v1/reasoning — synthetic read-only reasoning summary."""

    status: str
    confidence: float
    observation: str
    hypotheses: list[str] = Field(default_factory=list)
    recommendation: str = ""
    narrative: list[str] = Field(default_factory=list)


class TwinSimulateRequest(BaseModel):
    """POST /api/v1/twin/simulate body."""

    scenario: str = Field(
        default="CPU_OVERLOAD",
        description="Built-in twin scenario name (simulation only).",
    )
    cpu_percent: float = Field(default=40.0, ge=0, le=100)
    memory_percent: float = Field(default=50.0, ge=0, le=100)
    disk_percent: float = Field(default=30.0, ge=0, le=100)


class V1TwinSimulateResponse(BaseModel):
    """POST /api/v1/twin/simulate result (simulation only)."""

    scenario: str
    predicted_cpu: float
    predicted_memory: float
    predicted_disk: float
    stability: float
    risk: str
    confidence: float
    reasoning: str
    status: str = "simulation_only"


class V1ResearchResponse(BaseModel):
    """GET /api/v1/research."""

    discoveries: int
    observations: int
    context: str
    top_discovery: str | None = None
    confidence: float = 0.0
    status: str = "research_grade"


class V1PluginInfo(BaseModel):
    """One plugin descriptor for the public catalog."""

    id: str
    name: str
    version: str
    description: str = ""
    capabilities: list[str] = Field(default_factory=list)
    path: str = ""


class V1PluginsResponse(BaseModel):
    """GET /api/v1/plugins."""

    sdk_version: str
    plugins: list[V1PluginInfo]
    count: int
