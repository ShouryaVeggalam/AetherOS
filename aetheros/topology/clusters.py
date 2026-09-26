"""Cluster catalog helpers — clusters under datacenters from evidence.

Clusters appear when catalog metadata matches an observed datacenter, or
when an unassigned cluster is required for evidenced nodes without
explicit cluster placement.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from aetheros.topology.models import Cluster, Datacenter


def unassigned_cluster(datacenter: Datacenter) -> Cluster:
    """Placeholder cluster for nodes without explicit cluster metadata."""

    return Cluster(
        id=f"cluster-unassigned-{datacenter.id}",
        datacenter_id=datacenter.id,
        name=f"{datacenter.name} Default",
        node_count=0,
    )


def select_clusters(
    datacenters: Sequence[Datacenter],
    *,
    catalog: Sequence[Cluster] = (),
    require_unassigned_for: Sequence[str] = (),
    node_counts: Mapping[str, int] | None = None,
) -> tuple[Cluster, ...]:
    """Return catalog clusters for observed DCs, plus required unassigned."""

    dc_ids = {d.id for d in datacenters}
    dc_by_id = {d.id: d for d in datacenters}
    counts = dict(node_counts or {})
    by_id: dict[str, Cluster] = {}
    for cluster in catalog:
        if cluster.datacenter_id in dc_ids:
            count = counts.get(cluster.id, cluster.node_count)
            by_id[cluster.id] = Cluster(
                id=cluster.id,
                datacenter_id=cluster.datacenter_id,
                name=cluster.name,
                node_count=count,
            )
    for dc_id in require_unassigned_for:
        if dc_id not in dc_ids:
            continue
        cluster = unassigned_cluster(dc_by_id[dc_id])
        count = counts.get(cluster.id, 0)
        by_id.setdefault(
            cluster.id,
            Cluster(
                id=cluster.id,
                datacenter_id=cluster.datacenter_id,
                name=cluster.name,
                node_count=count,
            ),
        )
    return tuple(sorted(by_id.values(), key=lambda c: c.id))


def index_clusters(clusters: Sequence[Cluster]) -> Mapping[str, Cluster]:
    return {c.id: c for c in clusters}
