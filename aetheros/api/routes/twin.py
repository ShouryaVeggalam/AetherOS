"""Public API v1 — Digital Twin simulate (simulation only).

Clones a synthetic twin baseline, applies a built-in scenario, evaluates.
Never mutates live host state or twin core modules beyond calling public APIs.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException

from aetheros.api.schemas import TwinSimulateRequest, V1TwinSimulateResponse
from aetheros.graph.models import ResourceEdge, ResourceGraph, ResourceNode
from aetheros.policy_engine.models import TelemetrySnapshot
from aetheros.twin import apply_scenario, builtin_scenario, evaluate
from aetheros.twin.diff import diff_twins
from aetheros.twin.snapshot import clone_snapshot, create_snapshot

router = APIRouter(tags=["public-api-v1"])


@router.post("/twin/simulate", response_model=V1TwinSimulateResponse)
def post_twin_simulate(body: TwinSimulateRequest) -> V1TwinSimulateResponse:
    """Run one Digital Twin scenario on a cloned synthetic snapshot."""

    stamp = datetime.now(UTC)
    try:
        scenario = builtin_scenario(body.scenario, now=stamp)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    tel = TelemetrySnapshot(
        timestamp=stamp,
        cpu_percent=body.cpu_percent,
        memory_percent=body.memory_percent,
        disk_percent=body.disk_percent,
        battery_percent=None,
        process_count=1,
        top_processes=("api-twin",),
    )
    graph = ResourceGraph(
        nodes=(
            ResourceNode(
                "cpu", "CPU", "CPU", (("percent", f"{body.cpu_percent:.1f}"),), stamp
            ),
            ResourceNode(
                "memory",
                "Memory",
                "Memory",
                (("percent", f"{body.memory_percent:.1f}"),),
                stamp,
            ),
            ResourceNode(
                "disk",
                "Disk",
                "Disk",
                (("percent", f"{body.disk_percent:.1f}"),),
                stamp,
            ),
        ),
        edges=(ResourceEdge("cpu", "memory", "DEPENDS_ON", 0.4),),
    )
    baseline = create_snapshot(graph, tel, intent="API", now=stamp)
    simulated = apply_scenario(clone_snapshot(baseline, now=stamp), scenario)
    result = evaluate(baseline, simulated, scenario)
    _ = diff_twins(baseline, simulated)  # ensure diff path is exercised, unused

    return V1TwinSimulateResponse(
        scenario=scenario.name,
        predicted_cpu=float(result.predicted_cpu),
        predicted_memory=float(result.predicted_memory),
        predicted_disk=float(result.predicted_disk),
        stability=float(result.stability),
        risk=str(result.risk),
        confidence=float(result.confidence),
        reasoning=str(result.reasoning),
        status="simulation_only",
    )
