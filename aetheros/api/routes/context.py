"""Public API v1 — operational context (read-only).

Exposes a sanitized ContextEngine snapshot. Never mutates context stores.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from aetheros.api.schemas import V1ContextResponse
from aetheros.context import ContextEngine
from aetheros.policy_engine.models import TelemetrySnapshot

router = APIRouter(tags=["public-api-v1"])


@router.get("/context", response_model=V1ContextResponse)
def get_context(
    intent_name: str = "Balanced",
    cpu_percent: float = 35.0,
    memory_percent: float = 45.0,
    disk_percent: float = 30.0,
) -> V1ContextResponse:
    """Return a read-only operational context projection."""

    snap = TelemetrySnapshot(
        timestamp=datetime.now(UTC),
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        disk_percent=disk_percent,
        battery_percent=None,
        process_count=0,
        top_processes=(),
    )
    engine = ContextEngine()
    try:
        ctx = engine.refresh(snap, manual_intent=intent_name)
    except Exception:
        return V1ContextResponse(
            intent=intent_name,
            labels={"mode": "fallback"},
            notes=("context engine unavailable — placeholder projection",),
            source="fallback",
        )

    intent_obj = getattr(ctx, "intent", None)
    intent = str(
        getattr(intent_obj, "name", None)
        or getattr(intent_obj, "profile", None)
        or intent_name
    )
    labels: dict[str, str] = {
        "cpu_percent": f"{cpu_percent:.1f}",
        "memory_percent": f"{memory_percent:.1f}",
    }
    notes: list[str] = []
    pattern = getattr(ctx, "historical_pattern", None)
    if pattern is not None:
        notes.append(str(getattr(pattern, "summary", pattern)))
    explanation = getattr(ctx, "explanation", None) or getattr(ctx, "summary", None)
    if explanation:
        notes.append(str(explanation))
    return V1ContextResponse(
        intent=intent,
        labels=labels,
        notes=notes,
        source="context-engine",
    )
