"""Scenario library — transforms applied only to cloned twin snapshots.

REGION_OUTAGE · NODE_FAILURE · NETWORK_LATENCY · GPU_EXPANSION ·
WORKLOAD_SURGE · DISK_FAILURE · CUSTOM

Never touches live cloud, Kubernetes, Docker, or edge fleets.
"""

from __future__ import annotations

from aetheros.infra_twin.models import (
    SCENARIO_KINDS,
    InfrastructureSnapshot,
    TopologyNode,
    TwinScenario,
)


def library() -> tuple[TwinScenario, ...]:
    """Built-in scenario catalog for the dashboard."""

    return (
        TwinScenario(
            id="sc-region-outage",
            name="REGION_OUTAGE",
            description="Simulate loss of one availability region / AZ.",
            variables={"kind": "REGION_OUTAGE", "region": "us-east-1"},
        ),
        TwinScenario(
            id="sc-node-failure",
            name="NODE_FAILURE",
            description="Simulate disappearance of Kubernetes / compute nodes.",
            variables={"kind": "NODE_FAILURE", "count": 2},
        ),
        TwinScenario(
            id="sc-network-latency",
            name="NETWORK_LATENCY",
            description="Simulate elevated cross-region network latency.",
            variables={"kind": "NETWORK_LATENCY", "latency_delta_ms": 14.0},
        ),
        TwinScenario(
            id="sc-gpu-expansion",
            name="GPU_EXPANSION",
            description="Simulate doubling GPU / accelerator capacity.",
            variables={"kind": "GPU_EXPANSION", "capacity_factor": 2.0},
        ),
        TwinScenario(
            id="sc-workload-surge",
            name="WORKLOAD_SURGE",
            description="Simulate arrival of 500 new workloads (load shock).",
            variables={"kind": "WORKLOAD_SURGE", "workloads": 500},
        ),
        TwinScenario(
            id="sc-disk-failure",
            name="DISK_FAILURE",
            description="Simulate disk / volume failures on a subset of nodes.",
            variables={"kind": "DISK_FAILURE", "fraction": 0.15},
        ),
        TwinScenario(
            id="sc-custom",
            name="CUSTOM",
            description="Operator-defined variable mix (simulation only).",
            variables={"kind": "CUSTOM", "load_delta": 10.0, "latency_delta_ms": 2.0},
        ),
    )


def apply_scenario(
    snapshot: InfrastructureSnapshot,
    scenario: TwinScenario,
) -> InfrastructureSnapshot:
    """Apply scenario transforms to a **cloned** snapshot; return a new freeze.

    The input snapshot object is never mutated in place — callers should pass
    clones from ``clone_snapshot``.
    """

    kind = scenario.kind
    if kind not in SCENARIO_KINDS:
        raise ValueError(f"unsupported scenario kind: {kind}")
    if kind == "REGION_OUTAGE":
        return _region_outage(snapshot, scenario)
    if kind == "NODE_FAILURE":
        return _node_failure(snapshot, scenario)
    if kind == "NETWORK_LATENCY":
        return _network_latency(snapshot, scenario)
    if kind == "GPU_EXPANSION":
        return _gpu_expansion(snapshot, scenario)
    if kind == "WORKLOAD_SURGE":
        return _workload_surge(snapshot, scenario)
    if kind == "DISK_FAILURE":
        return _disk_failure(snapshot, scenario)
    return _custom(snapshot, scenario)


def _rebuild(
    snapshot: InfrastructureSnapshot,
    nodes: tuple[TopologyNode, ...],
) -> InfrastructureSnapshot:
    regions = tuple(sorted({n.region for n in nodes}))
    resources = tuple(sorted(f"{n.provider}:{n.kind}:{n.id}" for n in nodes))
    return InfrastructureSnapshot(
        id=snapshot.id,
        timestamp=snapshot.timestamp,
        topology=nodes,
        resources=resources,
        regions=regions,
    )


def _region_outage(
    snapshot: InfrastructureSnapshot,
    scenario: TwinScenario,
) -> InfrastructureSnapshot:
    region = str(scenario.variables.get("region") or "").strip()
    if not region and snapshot.regions:
        region = snapshot.regions[0]
    nodes = tuple(
        TopologyNode(
            id=n.id,
            kind=n.kind,
            region=n.region,
            provider=n.provider,
            capacity=n.capacity,
            load=n.load,
            latency_ms=n.latency_ms,
            available=False if n.region == region else n.available,
            metadata=dict(n.metadata),
        )
        for n in snapshot.topology
    )
    return _rebuild(snapshot, nodes)


def _node_failure(
    snapshot: InfrastructureSnapshot,
    scenario: TwinScenario,
) -> InfrastructureSnapshot:
    count = int(scenario.variables.get("count") or 1)
    count = max(0, count)
    victims = [
        n.id
        for n in snapshot.topology
        if n.available and n.kind in {"node", "compute", "vm"}
    ][:count]
    victim_set = set(victims)
    nodes = tuple(
        TopologyNode(
            id=n.id,
            kind=n.kind,
            region=n.region,
            provider=n.provider,
            capacity=n.capacity,
            load=n.load,
            latency_ms=n.latency_ms,
            available=False if n.id in victim_set else n.available,
            metadata=dict(n.metadata),
        )
        for n in snapshot.topology
    )
    return _rebuild(snapshot, nodes)


def _network_latency(
    snapshot: InfrastructureSnapshot,
    scenario: TwinScenario,
) -> InfrastructureSnapshot:
    delta = float(scenario.variables.get("latency_delta_ms") or 10.0)
    nodes = tuple(
        TopologyNode(
            id=n.id,
            kind=n.kind,
            region=n.region,
            provider=n.provider,
            capacity=n.capacity,
            load=n.load,
            latency_ms=n.latency_ms + delta,
            available=n.available,
            metadata=dict(n.metadata),
        )
        for n in snapshot.topology
    )
    return _rebuild(snapshot, nodes)


def _gpu_expansion(
    snapshot: InfrastructureSnapshot,
    scenario: TwinScenario,
) -> InfrastructureSnapshot:
    factor = float(scenario.variables.get("capacity_factor") or 2.0)
    factor = max(1.0, factor)
    nodes = tuple(
        TopologyNode(
            id=n.id,
            kind=n.kind,
            region=n.region,
            provider=n.provider,
            capacity=min(1000.0, n.capacity * factor),
            load=max(0.0, n.load / factor),
            latency_ms=n.latency_ms,
            available=n.available,
            metadata={**dict(n.metadata), "gpu_expanded": True},
        )
        for n in snapshot.topology
    )
    return _rebuild(snapshot, nodes)


def _workload_surge(
    snapshot: InfrastructureSnapshot,
    scenario: TwinScenario,
) -> InfrastructureSnapshot:
    workloads = int(scenario.variables.get("workloads") or 500)
    # Distribute load shock across available nodes (deterministic).
    available = [n for n in snapshot.topology if n.available]
    per_node = (
        workloads / max(1, len(available))
    ) * 0.02  # 500 → ~10% each if 10 nodes
    nodes = tuple(
        TopologyNode(
            id=n.id,
            kind=n.kind,
            region=n.region,
            provider=n.provider,
            capacity=n.capacity,
            load=min(100.0, n.load + per_node) if n.available else n.load,
            latency_ms=n.latency_ms + (2.0 if n.available else 0.0),
            available=n.available,
            metadata={**dict(n.metadata), "surge_workloads": workloads},
        )
        for n in snapshot.topology
    )
    return _rebuild(snapshot, nodes)


def _disk_failure(
    snapshot: InfrastructureSnapshot,
    scenario: TwinScenario,
) -> InfrastructureSnapshot:
    fraction = float(scenario.variables.get("fraction") or 0.15)
    fraction = max(0.0, min(1.0, fraction))
    candidates = [n for n in snapshot.topology if n.available]
    fail_count = int(round(len(candidates) * fraction))
    victims = {n.id for n in candidates[:fail_count]}
    nodes = tuple(
        TopologyNode(
            id=n.id,
            kind=n.kind,
            region=n.region,
            provider=n.provider,
            capacity=n.capacity,
            load=min(100.0, n.load + 15.0) if n.id in victims else n.load,
            latency_ms=n.latency_ms + (5.0 if n.id in victims else 0.0),
            available=False if n.id in victims else n.available,
            metadata={
                **dict(n.metadata),
                **({"disk_failed": True} if n.id in victims else {}),
            },
        )
        for n in snapshot.topology
    )
    return _rebuild(snapshot, nodes)


def _custom(
    snapshot: InfrastructureSnapshot,
    scenario: TwinScenario,
) -> InfrastructureSnapshot:
    load_delta = float(scenario.variables.get("load_delta") or 0.0)
    latency_delta = float(scenario.variables.get("latency_delta_ms") or 0.0)
    nodes = tuple(
        TopologyNode(
            id=n.id,
            kind=n.kind,
            region=n.region,
            provider=n.provider,
            capacity=n.capacity,
            load=min(100.0, max(0.0, n.load + load_delta)),
            latency_ms=max(0.0, n.latency_ms + latency_delta),
            available=n.available,
            metadata=dict(n.metadata),
        )
        for n in snapshot.topology
    )
    return _rebuild(snapshot, nodes)
