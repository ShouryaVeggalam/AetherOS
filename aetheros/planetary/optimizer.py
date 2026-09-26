"""Planetary optimizer — top-5 placement recommendations with trade-offs.

Deterministic ranking: score desc, then site_id asc. Labels explain
latency / cost / resilience / energy / balance trade-offs.

Recommendations only — never deploys or provisions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from aetheros.planetary.models import Candidate, PlacementSite, ScheduleDecision


def optimize_placements(
    candidates: Sequence[Candidate],
    *,
    sites: Sequence[PlacementSite] = (),
    top_n: int = 5,
) -> tuple[Candidate, ...]:
    """Return the top ``top_n`` candidates with trade-off labels attached."""

    if top_n < 1:
        raise ValueError("top_n must be >= 1")
    if not candidates:
        return ()

    site_map: Mapping[str, PlacementSite] = {s.site_id: s for s in sites}
    ranked = sorted(candidates, key=lambda c: (-c.score, c.site_id))
    top = ranked[:top_n]
    labels = _trade_off_labels(top, site_map)
    labeled: list[Candidate] = []
    for cand, label in zip(top, labels, strict=True):
        labeled.append(
            Candidate(
                region=cand.region,
                datacenter=cand.datacenter,
                cluster=cand.cluster,
                node=cand.node,
                score=cand.score,
                latency_ms=cand.latency_ms,
                availability=cand.availability,
                reasoning=cand.reasoning,
                trade_off=label,
            )
        )
    return tuple(labeled)


def explain_trade_offs(candidates: Sequence[Candidate]) -> tuple[str, ...]:
    """Human-readable trade-off summaries for the ranked set."""

    if not candidates:
        return ()
    out: list[str] = []
    for i, cand in enumerate(candidates):
        letter = chr(ord("A") + i)
        label = cand.trade_off or "Balanced placement"
        out.append(
            f"Candidate {letter} ({cand.site_id}): {label} — score {cand.score:.1f}"
        )
    return tuple(out)


def decision_from_ranked(
    workload: object,
    ranked: Sequence[Candidate],
    *,
    confidence: float,
    reasoning: str,
    simulations: Sequence[object] = (),
    rejected: Sequence[tuple[str, str]] = (),
) -> ScheduleDecision:
    """Build an immutable ``ScheduleDecision`` from ranked candidates."""

    from aetheros.planetary.models import GlobalWorkload, PlacementSimulation

    if not isinstance(workload, GlobalWorkload):
        raise TypeError("workload must be a GlobalWorkload")
    best = ranked[0] if ranked else None
    alternatives = tuple(ranked[1:]) if len(ranked) > 1 else ()
    sims = tuple(s for s in simulations if isinstance(s, PlacementSimulation))
    return ScheduleDecision(
        workload=workload,
        best_candidate=best,
        alternatives=alternatives,
        confidence=round(max(0.0, min(100.0, confidence)), 2),
        reasoning=reasoning,
        simulations=sims,
        rejected=tuple(rejected),
    )


def _trade_off_labels(
    ranked: Sequence[Candidate],
    site_map: Mapping[str, PlacementSite],
) -> tuple[str, ...]:
    """Assign unique trade-off labels deterministically from metrics."""

    if not ranked:
        return ()

    def latency_key(c: Candidate) -> float:
        return c.latency_ms

    def cost_key(c: Candidate) -> float:
        site = site_map.get(c.site_id)
        # Higher energy efficiency → lower effective cost.
        if site is None:
            return 100.0 - c.score
        return 100.0 - site.energy_efficiency

    def resilience_key(c: Candidate) -> float:
        site = site_map.get(c.site_id)
        if site is None:
            return -c.availability
        return -(site.regional_resilience)

    def energy_key(c: Candidate) -> float:
        site = site_map.get(c.site_id)
        if site is None:
            return 0.0
        return -site.energy_efficiency

    specialists: list[tuple[str, Candidate]] = []
    used: set[str] = set()

    for label, key_fn in (
        ("Best latency", latency_key),
        ("Lowest cost", cost_key),
        ("Highest resilience", resilience_key),
        ("Best energy efficiency", energy_key),
    ):
        ordered = sorted(ranked, key=lambda c: (key_fn(c), c.site_id))
        pick = next((c for c in ordered if c.site_id not in used), None)
        if pick is not None:
            specialists.append((label, pick))
            used.add(pick.site_id)

    label_by_id = {c.site_id: label for label, c in specialists}
    out: list[str] = []
    for i, cand in enumerate(ranked):
        if cand.site_id in label_by_id:
            out.append(label_by_id[cand.site_id])
        elif i == 0:
            out.append("Best overall score")
        else:
            out.append("Balanced alternative")
    return tuple(out)
