"""Planetary simulator — evaluate candidates on Infrastructure Digital Twin.

Clones twin snapshots, applies a CUSTOM placement load, and measures
latency · availability · CPU · memory · failure resilience.

Never modifies live infrastructure, Kubernetes, cloud, or Terraform state.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

from aetheros.infra_twin.clone import clone_snapshot
from aetheros.infra_twin.evaluator import (
    availability_pct,
    confidence_score,
    evaluate,
    mean_latency,
    mean_load,
    stability_score,
)
from aetheros.infra_twin.models import (
    InfrastructureSnapshot,
    TopologyNode,
    TwinScenario,
)
from aetheros.infra_twin.scenarios import apply_scenario
from aetheros.infra_twin.snapshot import demo_snapshot
from aetheros.planetary.models import (
    GlobalWorkload,
    PlacementSimulation,
    PlacementSite,
)


def simulate_site(
    workload: GlobalWorkload,
    site: PlacementSite,
    baseline: InfrastructureSnapshot,
    *,
    now: datetime | None = None,
) -> PlacementSimulation:
    """Clone the twin, apply a CUSTOM placement load for ``site``, evaluate."""

    stamp = now or datetime.now(UTC)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    cloned = clone_snapshot(baseline)
    cpu_delta = min(35.0, workload.cpu * 0.45)
    latency_delta = max(0.0, site.latency_ms * 0.05)
    scenario = TwinScenario(
        id=f"planetary-{site.site_id.replace('/', '-')}",
        name="CUSTOM",
        description=f"Planetary placement sim: {workload.id} → {site.site_id}",
        variables={
            "kind": "CUSTOM",
            "load_delta": round(cpu_delta, 2),
            "latency_delta_ms": round(latency_delta, 2),
            "target_region": site.region,
            "label": f"planetary:{workload.id}->{site.site_id}",
        },
    )
    after = apply_scenario(cloned, scenario)
    result = evaluate(after, scenario, baseline=baseline)

    # Blend site census with twin predictions — never mutate live state.
    predicted_latency = round(
        site.latency_ms * (1.0 + max(0.0, result.cpu - 50.0) / 250.0),
        2,
    )
    avail = round(
        min(100.0, 0.55 * availability_pct(after) + 0.45 * site.cluster_health),
        2,
    )
    cpu = round(min(100.0, mean_load(after)), 2)
    memory = round(min(100.0, result.memory), 2)
    resilience = round(
        min(
            100.0,
            0.5 * site.regional_resilience
            + 0.3 * stability_score(after)
            + 0.2 * (0.0 if site.degraded else 100.0),
        ),
        2,
    )
    twin_conf = confidence_score(after, baseline_nodes=baseline.node_count)
    return PlacementSimulation(
        site_id=site.site_id,
        latency_ms=predicted_latency,
        availability=avail,
        cpu=cpu,
        memory=memory,
        failure_resilience=resilience,
        twin_confidence=round(twin_conf, 2),
    )


def simulate_sites(
    workload: GlobalWorkload,
    sites: Sequence[PlacementSite],
    baseline: InfrastructureSnapshot | None = None,
    *,
    now: datetime | None = None,
) -> tuple[PlacementSimulation, ...]:
    """Simulate each candidate independently on cloned twin snapshots."""

    snap = baseline or demo_snapshot(timestamp=now)
    return tuple(simulate_site(workload, site, snap, now=now) for site in sites)


def baseline_from_sites(
    sites: Sequence[PlacementSite],
    *,
    now: datetime | None = None,
) -> InfrastructureSnapshot:
    """Build a minimal infra-twin baseline from planetary site census."""

    stamp = now or datetime.now(UTC)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    if not sites:
        return demo_snapshot(timestamp=stamp)
    nodes: list[TopologyNode] = []
    for site in sites:
        load = max(
            0.0,
            min(
                100.0,
                100.0 - min(site.cpu_available, site.memory_available),
            ),
        )
        nodes.append(
            TopologyNode(
                id=site.site_id.replace("/", "-"),
                kind="node",
                region=site.region,
                provider=str(site.metadata.get("provider", "planetary")),
                capacity=100.0,
                load=load,
                latency_ms=site.latency_ms,
                available=not site.degraded,
                metadata={
                    "datacenter": site.datacenter,
                    "cluster": site.cluster,
                    "node": site.node,
                    "energy": f"{site.energy_efficiency:.1f}",
                    "resilience": f"{site.regional_resilience:.1f}",
                },
            )
        )
    topology = tuple(nodes)
    regions = tuple(sorted({n.region for n in topology}))
    resources = tuple(sorted(f"{n.provider}:{n.kind}:{n.id}" for n in topology))
    return InfrastructureSnapshot(
        id="planetary-twin-baseline",
        timestamp=stamp,
        topology=topology,
        resources=resources,
        regions=regions,
    )


def twin_latency_probe(snapshot: InfrastructureSnapshot) -> float:
    """Read-only mean latency probe against a twin snapshot."""

    return mean_latency(snapshot)
