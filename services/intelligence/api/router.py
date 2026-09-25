"""Aggregate `/v9` General Intelligence Infrastructure router."""

from __future__ import annotations

from fastapi import APIRouter

from services.intelligence.api import cognition

router = APIRouter(prefix="/v9")
router.include_router(cognition.router)
