"""Public API v1 — health probe.

Read-only liveness. Does not touch intelligence engines.
"""

from __future__ import annotations

from fastapi import APIRouter

from aetheros import __version__
from aetheros.api.schemas import V1HealthResponse

router = APIRouter(tags=["public-api-v1"])


@router.get("/health", response_model=V1HealthResponse)
def get_health() -> V1HealthResponse:
    """Liveness probe for the versioned public API."""

    return V1HealthResponse(
        status="ok",
        version=__version__,
        api_version="v1",
        mode="read-only",
        control="human",
    )
