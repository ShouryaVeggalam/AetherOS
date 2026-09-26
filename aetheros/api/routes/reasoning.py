"""Public API v1 — reasoning summary (read-only).

Runs one CognitiveRuntime cycle on synthetic telemetry for a JSON summary.
Does not modify cognition core modules.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter

from aetheros.api.schemas import V1ReasoningResponse
from aetheros.cognition import CognitiveMemory, CognitiveRuntime
from aetheros.intent.profiles import PROFILES
from aetheros.policy_engine.models import TelemetrySnapshot

router = APIRouter(tags=["public-api-v1"])


@router.get("/reasoning", response_model=V1ReasoningResponse)
def get_reasoning(
    cpu_percent: float = 72.0,
    memory_percent: float = 55.0,
    disk_percent: float = 40.0,
    intent_name: str = "Balanced",
) -> V1ReasoningResponse:
    """Return a read-only reasoning summary for synthetic telemetry."""

    snap = TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        disk_percent=disk_percent,
        battery_percent=None,
        process_count=2,
        top_processes=("python", "cursor"),
    )
    intent = PROFILES.get(intent_name) or PROFILES["Balanced"]
    # Match by case-insensitive name when key lookup fails.
    if intent_name not in PROFILES:
        for profile in PROFILES.values():
            if profile.name.lower() == intent_name.lower():
                intent = profile
                break

    runtime = CognitiveRuntime(
        memory=CognitiveMemory(Path("data/cognition_memory_api_v1.db"))
    )
    try:
        report = runtime.reason(snap, intent, history=())
    except Exception:
        return V1ReasoningResponse(
            status="unavailable",
            confidence=0.0,
            observation="reasoning engine unavailable",
            hypotheses=(),
            recommendation="",
            narrative=(),
        )

    observation = str(getattr(getattr(report, "observation", None), "summary", ""))
    hyp_titles: list[str] = []
    hypotheses = getattr(report, "hypotheses", None)
    items = getattr(hypotheses, "hypotheses", ()) if hypotheses is not None else ()
    for hyp in items:
        hyp_titles.append(str(getattr(hyp, "title", hyp)))

    recommendation = ""
    plans = getattr(report, "plans", None)
    if plans is not None and getattr(plans, "recommended", None) is not None:
        recommendation = str(getattr(plans.recommended, "summary", plans.recommended))

    narrative = [str(n) for n in (getattr(report, "narrative", ()) or ())]
    return V1ReasoningResponse(
        status=str(getattr(report, "status", "ok")),
        confidence=float(getattr(report, "confidence", 0.0)),
        observation=observation or "n/a",
        hypotheses=hyp_titles,
        recommendation=recommendation,
        narrative=narrative,
    )
