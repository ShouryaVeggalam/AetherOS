"""Planetary constraint engine — reject invalid sites before scoring.

Hard gates only. Never deploys, provisions, or mutates infrastructure.
Kinds: REGION_LOCK · LATENCY_MAX · REQUIRE_GPU · AVOID_DEGRADED ·
ENERGY_PRIORITY · COMPLIANCE_REGION.
"""

from __future__ import annotations

from collections.abc import Sequence

from aetheros.planetary.models import (
    GlobalWorkload,
    PlacementSite,
    PlanetaryConstraint,
)


def check_constraints(
    workload: GlobalWorkload,
    site: PlacementSite,
    constraints: Sequence[PlanetaryConstraint] = (),
) -> tuple[bool, str]:
    """Return ``(accepted, reason)`` for one workload→site pair."""

    # Intrinsic capacity gate (always on).
    if workload.cpu > site.cpu_available + 1e-9:
        return False, "insufficient CPU capacity"
    if workload.memory > site.memory_available + 1e-9:
        return False, "insufficient memory capacity"
    if workload.gpu > site.gpu_available + 1e-9:
        return False, "insufficient GPU capacity"

    # Soft region preference is advisory only; REGION_LOCK below is hard.
    for constraint in constraints:
        ok, reason = _apply_one(workload, site, constraint)
        if not ok:
            return False, reason
    return True, "ok"


def filter_candidates(
    workload: GlobalWorkload,
    sites: Sequence[PlacementSite],
    constraints: Sequence[PlanetaryConstraint] = (),
) -> tuple[tuple[PlacementSite, ...], tuple[tuple[str, str], ...]]:
    """Split sites into accepted candidates and rejected ``(site_id, reason)``."""

    accepted: list[PlacementSite] = []
    rejected: list[tuple[str, str]] = []
    for site in sites:
        ok, reason = check_constraints(workload, site, constraints)
        if ok:
            accepted.append(site)
        else:
            rejected.append((site.site_id, reason))
    return tuple(accepted), tuple(rejected)


def _apply_one(
    workload: GlobalWorkload,
    site: PlacementSite,
    constraint: PlanetaryConstraint,
) -> tuple[bool, str]:
    kind = constraint.kind
    if kind == "REGION_LOCK":
        region = str(constraint.value).strip().lower()
        if not region:
            return False, "REGION_LOCK value empty"
        if site.region.strip().lower() != region:
            return False, f"REGION_LOCK requires {region}"
        return True, "ok"
    if kind == "LATENCY_MAX":
        limit = float(constraint.value) if constraint.value != "" else workload.latency_target
        if site.latency_ms > limit + 1e-9:
            return False, f"LATENCY_MAX exceeded ({site.latency_ms:.1f}>{limit:.1f})"
        return True, "ok"
    if kind == "REQUIRE_GPU":
        need = float(constraint.value) if constraint.value != "" else 1.0
        need = max(need, workload.gpu)
        if site.gpu_available + 1e-9 < need:
            return False, "REQUIRE_GPU not satisfied"
        return True, "ok"
    if kind == "AVOID_DEGRADED":
        if site.degraded:
            return False, "AVOID_DEGRADED rejects degraded site"
        return True, "ok"
    if kind == "ENERGY_PRIORITY":
        threshold = float(constraint.value) if constraint.value != "" else 75.0
        if site.energy_efficiency + 1e-9 < threshold:
            return False, f"ENERGY_PRIORITY requires efficiency ≥ {threshold:.0f}"
        return True, "ok"
    if kind == "COMPLIANCE_REGION":
        tag = str(constraint.value).strip().lower()
        if not tag:
            return False, "COMPLIANCE_REGION value empty"
        tags = {t.strip().lower() for t in site.compliance_tags}
        if tag not in tags and site.region.strip().lower() != tag:
            return False, f"COMPLIANCE_REGION requires {tag}"
        return True, "ok"
    return False, f"unknown constraint {kind}"
