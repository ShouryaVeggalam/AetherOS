"""Public API v1 — research summary (read-only / research-grade).

Uses ResearchIntelligenceEngine when possible; falls back to a structured empty report.
"""

from __future__ import annotations

from fastapi import APIRouter

from aetheros.api.schemas import V1ResearchResponse

router = APIRouter(tags=["public-api-v1"])


@router.get("/research", response_model=V1ResearchResponse)
def get_research() -> V1ResearchResponse:
    """Return a research-grade summary from the intelligence engine."""

    try:
        from aetheros.research import ResearchIntelligenceEngine

        engine = ResearchIntelligenceEngine(min_evidence=1)
        report = engine.generate(context="public-api", write_markdown=False)
    except Exception:
        return V1ResearchResponse(
            discoveries=0,
            observations=0,
            context="unavailable",
            top_discovery=None,
            confidence=0.0,
            status="unavailable",
        )

    discoveries = tuple(getattr(report, "discoveries", ()) or ())
    observations = tuple(getattr(report, "observations", ()) or ())
    top = discoveries[0] if discoveries else None
    top_title = None
    confidence = 0.0
    if top is not None:
        top_title = str(getattr(top, "title", getattr(top, "summary", top)))
        confidence = float(getattr(top, "confidence", 0.0))
    return V1ResearchResponse(
        discoveries=len(discoveries),
        observations=len(observations),
        context=str(getattr(report, "context", "api")),
        top_discovery=top_title,
        confidence=confidence,
        status="research_grade",
    )
