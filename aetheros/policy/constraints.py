"""Policy Studio constraints — advisory overlays for Twin / Scheduler / Consensus.

Produces immutable constraint descriptors from matched evaluation results.
Never mutates scheduler, twin, or consensus engines.
"""

from __future__ import annotations

from dataclasses import dataclass

from aetheros.policy.models import EvaluationResult


@dataclass(frozen=True, slots=True)
class GovernanceConstraint:
    """One read-only constraint derived from a matched policy rule."""

    source_policy_id: str
    source_version: int
    kind: str  # "filter_recommendation" | "region_affinity" | "simulation" | "research"
    detail: str
    action: str


def constraints_from_results(
    results: tuple[EvaluationResult, ...],
) -> tuple[GovernanceConstraint, ...]:
    """Map matched evaluation results onto governance constraint descriptors."""

    out: list[GovernanceConstraint] = []
    for result in results:
        if not result.matched:
            continue
        action = (result.action or "").strip()
        lower = action.lower()
        if "reject" in lower or "filter" in lower:
            kind = "filter_recommendation"
        elif "region" in lower or "remain" in lower or "affinity" in lower:
            kind = "region_affinity"
        elif "simulat" in lower or "twin" in lower:
            kind = "simulation"
        elif "research" in lower or "experiment" in lower:
            kind = "research"
        else:
            kind = "simulation"
        out.append(
            GovernanceConstraint(
                source_policy_id=result.policy.id,
                source_version=result.policy.version,
                kind=kind,
                detail=result.explanation,
                action=action,
            )
        )
    return tuple(out)


def filter_recommendations(
    recommendations: tuple[str, ...],
    results: tuple[EvaluationResult, ...],
) -> tuple[str, ...]:
    """Drop recommendation titles rejected by matched policy actions.

    Matching is case-insensitive substring against the action text after
    ``reject`` / ``block`` / ``deny``. Unmatched recommendations pass through.
    """

    rejects: list[str] = []
    for result in results:
        if not result.matched:
            continue
        action = result.action.lower()
        for prefix in ("reject ", "block ", "deny "):
            if prefix in action:
                target = action.split(prefix, 1)[1].strip()
                if target:
                    rejects.append(target)
    if not rejects:
        return recommendations
    kept: list[str] = []
    for title in recommendations:
        lowered = title.lower()
        if any(r in lowered for r in rejects):
            continue
        kept.append(title)
    return tuple(kept)
