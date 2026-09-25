"""FastAPI surface for AetherOS (read-only).

Exposes cognitive reports, knowledge catalogs, and Horizon planetary
intelligence. Never executes OS actions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from aetheros import __version__
from aetheros.api.schemas import (
    AnomalyOut,
    FabricOverview,
    GenerationOut,
    HealthResponse,
    InfinityOverview,
    LayerStatusOut,
    PipelineStageOut,
    ResilienceOut,
    SentinelOverview,
)
from aetheros.cognition import CognitiveMemory, CognitiveRuntime
from aetheros.fabric import FabricRuntime
from aetheros.genesis import GenesisRuntime
from aetheros.genesis.knowledge_base import KnowledgeBase
from aetheros.genesis.theorem_store import TheoremStore
from aetheros.horizon import (
    FailureScenario,
    HorizonRuntime,
    ResilienceSimulator,
    WorldGraph,
)
from aetheros.infinity import InfinityRuntime
from aetheros.intent.models import IntentProfile
from aetheros.intent.profiles import PROFILES
from aetheros.knowledge import CORE_ONTOLOGY, RESOURCE_TYPES, WORKLOAD_EDGES
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.sentinel import SentinelRuntime


class TelemetryIn(BaseModel):
    """Inbound telemetry for a cognitive reasoning request."""

    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    disk_percent: float = Field(ge=0, le=100)
    battery_percent: float | None = None
    top_processes: list[str] = Field(default_factory=list)
    intent_name: str = "Balanced"


def create_app(
    *,
    memory_db: Path | None = None,
) -> FastAPI:
    """Build the FastAPI application (recommendation-only API)."""

    app = FastAPI(
        title="AetherOS API",
        version=__version__,
        description=(
            "Explainable Operating Intelligence API (Infinity ∞). "
            "Read-only / simulation-first. Humans approve actions. "
            "CELESTRA GII Module 1 exposes cognition under `/v9`."
        ),
        openapi_tags=[
            {
                "name": "gii-cognition",
                "description": (
                    "CELESTRA GII v9 — Cognition Engine "
                    "(understand · decompose · allocate)."
                ),
            },
        ],
    )
    from services.intelligence.api.router import router as gii_v9_router

    app.include_router(gii_v9_router)
    runtime = CognitiveRuntime(
        memory=CognitiveMemory(memory_db or Path("data/cognition_memory.db"))
    )
    horizon = HorizonRuntime()
    data_dir = memory_db.parent if memory_db is not None else Path("data")
    genesis = GenesisRuntime(
        knowledge=KnowledgeBase(data_dir / "genesis_knowledge.db"),
        theorems=TheoremStore(data_dir / "genesis_theorems.db"),
    )
    sentinel = SentinelRuntime()
    fabric = FabricRuntime(knowledge=KnowledgeBase(data_dir / "genesis_knowledge.db"))
    infinity = InfinityRuntime(
        horizon=horizon,
        genesis=genesis,
        sentinel=sentinel,
        fabric=fabric,
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        """Liveness probe."""

        return HealthResponse(
            status="ok",
            version=__version__,
            mode="simulation-only",
            control="human",
        )

    @app.get("/knowledge/ontology")
    def ontology() -> list[dict[str, Any]]:
        """Return the public systems ontology."""

        return [
            {
                "concept_id": c.concept_id,
                "domain": c.domain,
                "label": c.label,
                "summary": c.summary,
                "tags": list(c.tags),
            }
            for c in CORE_ONTOLOGY
        ]

    @app.get("/knowledge/resources")
    def resources() -> list[dict[str, str]]:
        """Return resource type catalog."""

        return [
            {
                "kind": r.kind,
                "label": r.label,
                "unit": r.unit,
                "description": r.description,
            }
            for r in RESOURCE_TYPES
        ]

    @app.get("/knowledge/workload-edges")
    def workload_edges() -> list[dict[str, Any]]:
        """Return static workload→resource edges."""

        return [
            {
                "workload_id": e.workload_id,
                "relation": e.relation,
                "resource": e.resource,
                "intensity": e.intensity,
                "note": e.note,
            }
            for e in WORKLOAD_EDGES
        ]

    @app.get("/memory/facts")
    def memory_facts() -> list[dict[str, Any]]:
        """List structured cognitive memory facts (no private content)."""

        return [
            {
                "fact_key": f.fact_key,
                "subject": f.subject,
                "predicate": f.predicate,
                "object": f.object,
                "confidence": f.confidence,
                "source": f.source,
                "notes": f.notes,
            }
            for f in runtime.memory.list_facts()
        ]

    @app.post("/cognition/reason")
    def reason(body: TelemetryIn) -> dict[str, Any]:
        """Run one cognitive cycle and return a JSON report."""

        snapshot = TelemetrySnapshot(
            timestamp=datetime.now(UTC),
            cpu_percent=body.cpu_percent,
            memory_percent=body.memory_percent,
            disk_percent=body.disk_percent,
            battery_percent=body.battery_percent,
            process_count=len(body.top_processes),
            top_processes=tuple(body.top_processes),
        )
        intent = _intent_by_name(body.intent_name)
        report = runtime.reason(snapshot, intent, history=())
        return _report_to_dict(report)

    @app.get("/world")
    def world() -> dict[str, Any]:
        """Planetary census and sample world summary."""

        report = horizon.observe()
        census = report.world.census
        return {
            "world_health": census.world_health,
            "regions": census.regions,
            "datacenters": census.datacenters,
            "clusters": census.clusters,
            "nodes": census.nodes,
            "status": report.status,
            "sample_nodes": report.world.node_count,
            "sample_edges": report.world.edge_count,
        }

    @app.get("/regions")
    def regions() -> list[dict[str, Any]]:
        """List sample regions with health."""

        return [
            {
                "id": r.node_id,
                "name": r.name,
                "health": r.health,
                "capacity_score": r.capacity_score,
            }
            for r in horizon.graph.regions()
        ]

    @app.get("/latency")
    def latency() -> list[dict[str, Any]]:
        """Region-pair latency estimates (no live probes)."""

        estimates = horizon.latency_engine.estimate_regions(horizon.graph)
        return [
            {
                "source": e.source_id,
                "target": e.target_id,
                "distance_km": e.distance_km,
                "network": e.network,
                "estimated_ms": e.estimated_ms,
                "reliability": e.reliability,
                "confidence": e.confidence,
                "explanation": e.explanation,
            }
            for e in estimates
        ]

    @app.get("/resilience")
    def resilience(
        target_id: str = "region.eu",
        capacity_loss_pct: float = 15.0,
    ) -> dict[str, Any]:
        """Simulate a failure scenario (default: Europe −15% capacity)."""

        sim = ResilienceSimulator()
        report = sim.simulate(
            horizon.graph,
            FailureScenario(
                kind="region_outage",
                target_id=target_id,
                capacity_loss_pct=capacity_loss_pct,
                description=f"{target_id} loses {capacity_loss_pct:.0f}% capacity.",
            ),
        )
        return {
            "scenario": {
                "kind": report.scenario.kind,
                "target_id": report.scenario.target_id,
                "capacity_loss_pct": report.scenario.capacity_loss_pct,
                "description": report.scenario.description,
            },
            "remaining_capacity_pct": report.remaining_capacity_pct,
            "cluster_health": report.cluster_health,
            "global_stability": report.global_stability,
            "world_health_after": report.world_health_after,
            "affected_nodes": list(report.affected_nodes),
            "explanation": report.explanation,
            "confidence": report.confidence,
        }

    @app.get("/capacity")
    def capacity() -> dict[str, Any]:
        """Multi-horizon capacity forecasts."""

        plan = horizon.capacity_planner.plan(horizon.graph)
        return {
            "overall_confidence": plan.overall_confidence,
            "narrative": list(plan.narrative),
            "forecasts": [
                {
                    "resource": f.resource,
                    "horizon": f.horizon,
                    "baseline": f.baseline,
                    "projected": f.projected,
                    "growth_pct": f.growth_pct,
                    "explanation": f.explanation,
                    "confidence": f.confidence,
                }
                for f in plan.forecasts
            ],
        }

    @app.get("/graph")
    def graph() -> dict[str, Any]:
        """Full sample world graph JSON."""

        return WorldGraph().to_dict()

    @app.get("/genesis")
    def genesis_overview() -> dict[str, Any]:
        """Genesis research overview (simulation-only cycle)."""

        report = genesis.research(experiment_runs=12)
        return {
            "verified_knowledge": report.census.verified_knowledge,
            "active_experiments": report.census.active_experiments,
            "largest_evidence_set": report.largest_title,
            "simulations": report.largest_simulations,
            "confidence": report.largest_confidence,
            "status": report.status,
            "question": report.question,
            "local_knowledge": len(report.knowledge),
            "verified_this_cycle": len(report.verified),
            "rejected_this_cycle": len(report.rejected),
        }

    @app.get("/genesis/knowledge")
    def genesis_knowledge() -> list[dict[str, Any]]:
        """List verified knowledge records."""

        return [
            {
                "knowledge_id": k.knowledge_id,
                "statement": k.statement,
                "evidence": list(k.evidence),
                "simulation_count": k.simulation_count,
                "confidence": k.confidence,
                "clusters_verified": k.clusters_verified,
                "source": k.source,
                "tags": list(k.tags),
            }
            for k in genesis.knowledge.list_knowledge()
        ]

    @app.get("/genesis/theorems")
    def genesis_theorems() -> list[dict[str, Any]]:
        """List verified discoveries / theorems."""

        return [
            {
                "theorem_id": t.theorem_id,
                "title": t.title,
                "statement": t.statement,
                "simulation_count": t.simulation_count,
                "confidence": t.confidence,
                "evidence": list(t.evidence),
            }
            for t in genesis.theorems.list_theorems()
        ]

    @app.get("/genesis/ontology")
    def genesis_ontology() -> dict[str, Any]:
        """Genesis computing ontology catalog."""

        from aetheros.ontology import (
            INTENT_ENTITIES,
            RESOURCE_ENTITIES,
            SEED_RELATIONS,
            WORKLOAD_ENTITIES,
        )

        return {
            "resources": [
                {
                    "id": r.entity_id,
                    "kind": r.kind,
                    "label": r.label,
                    "unit": r.unit,
                }
                for r in RESOURCE_ENTITIES
            ],
            "workloads": [
                {"id": w.entity_id, "label": w.label} for w in WORKLOAD_ENTITIES
            ],
            "intents": [{"id": i.entity_id, "label": i.label} for i in INTENT_ENTITIES],
            "relationships": [
                {
                    "id": rel.relation_id,
                    "source": rel.source_id,
                    "relation": rel.relation,
                    "target": rel.target_id,
                    "weight": rel.weight,
                }
                for rel in SEED_RELATIONS
            ],
        }

    @app.get("/sentinel", response_model=SentinelOverview)
    def sentinel_overview(
        cpu_percent: float = 72.0,
        memory_percent: float = 55.0,
        disk_percent: float = 40.0,
        battery_percent: float | None = 80.0,
    ) -> SentinelOverview:
        """Sentinel resilience overview for a synthetic snapshot."""

        snap = TelemetrySnapshot(
            timestamp=datetime.now(UTC),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            battery_percent=battery_percent,
            process_count=4,
            top_processes=("Cursor", "Indexer", "chrome", "python"),
        )
        report = sentinel.observe(snap)
        return SentinelOverview(
            health=report.health,
            risk=report.risk,
            active_anomalies=len(report.anomalies),
            predicted_cascade=(
                "None" if not report.cascade.active else report.cascade.summary
            ),
            recommended_strategy=report.recommended_strategy,
            confidence=report.confidence,
            status=report.status,
            resilience=ResilienceOut(
                health=report.resilience.health,
                stability=report.resilience.stability,
                redundancy=report.resilience.redundancy,
                risk=report.resilience.risk,
                explanation=report.resilience.explanation,
            ),
        )

    @app.get("/sentinel/anomalies", response_model=list[AnomalyOut])
    def sentinel_anomalies(
        cpu_percent: float = 92.0,
        memory_percent: float = 60.0,
    ) -> list[AnomalyOut]:
        """Detect anomalies for a provided snapshot."""

        snap = TelemetrySnapshot(
            timestamp=datetime.now(UTC),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=40.0,
            battery_percent=70.0,
            process_count=5,
            top_processes=("Indexer", "Cursor"),
        )
        report = sentinel.observe(snap)
        return [
            AnomalyOut(
                id=a.anomaly_id,
                kind=a.kind,
                severity=a.severity,
                title=a.title,
                description=a.description,
                metric=a.metric,
                value=a.value,
            )
            for a in report.anomalies
        ]

    @app.get("/sentinel/graph")
    def sentinel_graph() -> dict[str, Any]:
        """Dependency graph used for cascade simulation."""

        return sentinel.graph.to_dict()

    @app.get("/infinity", response_model=InfinityOverview)
    def infinity_overview() -> InfinityOverview:
        """Infinity platform overview — generations, pipeline, layer status."""

        report = infinity.observe()
        return InfinityOverview(
            identity=report.identity,
            status=report.status,
            generation_count=report.generation_count,
            layers_ready=report.layers_ready,
            principles=list(report.principles),
            pipeline=[
                PipelineStageOut(
                    stage_id=s.stage_id,
                    name=s.name,
                    package=s.package,
                    description=s.description,
                    produces=s.produces,
                )
                for s in report.pipeline
            ],
            generations=[
                GenerationOut(
                    version=g.version,
                    codename=g.codename,
                    package=g.package,
                    summary=g.summary,
                    principles=list(g.principles),
                )
                for g in report.generations
            ],
            layers=[
                LayerStatusOut(
                    name=layer.name,
                    ready=layer.ready,
                    detail=layer.detail,
                )
                for layer in report.layers
            ],
        )

    @app.get("/fabric", response_model=FabricOverview)
    def fabric_overview() -> FabricOverview:
        """Aether Fabric universal overview."""

        report = fabric.observe()
        return FabricOverview(
            connected_nodes=report.connected_nodes,
            regions=report.census.regions,
            datacenters=report.census.datacenters,
            clusters=report.census.clusters,
            synchronization=report.synchronization,
            global_health=report.global_health,
            status=report.status,
            sample_graph_nodes=report.graph_nodes,
            sample_graph_edges=report.graph_edges,
        )

    @app.get("/federation")
    def federation() -> dict[str, Any]:
        """Federation health and member snapshots."""

        report = fabric.observe()
        fed = report.federation
        return {
            "member_count": fed.member_count,
            "synced_count": fed.synced_count,
            "synchronization": fed.synchronization,
            "mean_health": fed.mean_health,
            "stale_nodes": list(fed.stale_nodes),
            "snapshots": [
                {
                    "node_id": s.node_id,
                    "cpu": s.cpu,
                    "memory": s.memory,
                    "gpu": s.gpu,
                    "network": s.network,
                    "health": s.health,
                    "version": s.version,
                    "timestamp": s.timestamp.isoformat(),
                }
                for s in fabric.federation.snapshots()
            ],
        }

    @app.get("/twin")
    def twin() -> dict[str, Any]:
        """Global digital twin scenario outcomes."""

        report = fabric.observe()
        plan = report.twin.plan
        return {
            "status": report.twin.status,
            "rationale": plan.rationale,
            "recommended": (
                None
                if plan.recommended is None
                else {
                    "title": plan.recommended.scenario.title,
                    "kind": plan.recommended.scenario.kind,
                    "capacity": plan.recommended.capacity,
                    "stability": plan.recommended.stability,
                    "latency": plan.recommended.latency,
                    "risk": plan.recommended.risk,
                    "explanation": plan.recommended.explanation,
                }
            ),
            "outcomes": [
                {
                    "title": o.scenario.title,
                    "kind": o.scenario.kind,
                    "capacity": o.capacity,
                    "stability": o.stability,
                    "latency": o.latency,
                    "risk": o.risk,
                }
                for o in plan.outcomes
            ],
        }

    @app.get("/fabric/graph")
    def fabric_graph() -> dict[str, Any]:
        """Universal fabric graph JSON."""

        return fabric.graph.to_dict()

    @app.get("/knowledge")
    def knowledge_network() -> dict[str, Any]:
        """Fabric knowledge network (verified Genesis records)."""

        records = fabric.knowledge.list_knowledge()
        return {
            "count": len(records),
            "records": [
                {
                    "knowledge_id": k.knowledge_id,
                    "statement": k.statement,
                    "confidence": k.confidence,
                    "simulation_count": k.simulation_count,
                    "evidence": list(k.evidence),
                }
                for k in records
            ],
        }

    return app


def _intent_by_name(name: str) -> IntentProfile:
    """Resolve an intent profile by name with Balanced fallback."""

    for profile in PROFILES.values():
        if profile.name.lower() == name.lower():
            return profile
    return PROFILES["Balanced"]


def _report_to_dict(report: object) -> dict[str, Any]:
    """Serialize CognitiveReport for JSON responses."""

    from aetheros.reasoning.explain import CognitiveReport as CR

    assert isinstance(report, CR)
    verified = None
    if report.verified.result is not None:
        hyp = report.verified.result.hypothesis
        verified = {
            "title": hyp.title,
            "description": hyp.description,
            "support_score": report.verified.result.support_score,
            "reasons": list(report.verified.result.reasons),
        }
    plans = None
    if report.plans is not None:
        plans = {
            "recommended": (
                None
                if report.plans.recommended is None
                else {
                    "title": report.plans.recommended.title,
                    "score": report.plans.recommended.score,
                    "summary": report.plans.recommended.summary,
                }
            ),
            "all": [
                {"title": p.title, "score": p.score, "plan_id": p.plan_id}
                for p in report.plans.plans
            ],
        }
    return {
        "observation": {
            "kind": report.observation.kind,
            "summary": report.observation.summary,
            "metric": report.observation.metric,
            "value": report.observation.value,
        },
        "hypotheses": [
            {
                "id": h.hypothesis_id,
                "title": h.title,
                "probability": h.probability,
                "description": h.description,
            }
            for h in report.hypotheses.hypotheses
        ],
        "verified": verified,
        "plans": plans,
        "graph": {
            "nodes": len(report.graph.nodes),
            "edges": len(report.graph.edges),
            "sample_edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "relation": e.relation,
                    "weight": e.weight,
                    "evidence": e.evidence,
                }
                for e in report.graph.edges[:12]
            ],
        },
        "narrative": list(report.narrative),
        "confidence": report.confidence,
        "status": report.status,
    }


app = create_app()
