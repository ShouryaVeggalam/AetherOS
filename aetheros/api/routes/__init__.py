"""Public API v1 routers — versioned read-only FastAPI surface."""

from __future__ import annotations

from fastapi import APIRouter

from aetheros.api.routes import (
    context,
    graph,
    health,
    plugins,
    reasoning,
    research,
    twin,
)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health.router)
api_v1_router.include_router(context.router)
api_v1_router.include_router(graph.router)
api_v1_router.include_router(reasoning.router)
api_v1_router.include_router(twin.router)
api_v1_router.include_router(research.router)
api_v1_router.include_router(plugins.router)

__all__ = ["api_v1_router"]
