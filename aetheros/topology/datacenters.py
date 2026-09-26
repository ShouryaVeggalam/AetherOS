"""Datacenter catalog helpers — placement under regions from evidence.

Datacenters are created only when catalog metadata is supplied for an
observed region, or when a deterministic unassigned DC is required to
host evidenced clusters/nodes (never speculative geography).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from aetheros.topology.models import Datacenter, Region


def unassigned_datacenter(region: Region) -> Datacenter:
    """Placeholder DC for nodes in a region without explicit DC metadata."""

    return Datacenter(
        id=f"dc-unassigned-{region.id}",
        region_id=region.id,
        name=f"{region.name} Unassigned",
        capacity=0,
    )


def select_datacenters(
    regions: Sequence[Region],
    *,
    catalog: Sequence[Datacenter] = (),
    require_unassigned_for: Sequence[str] = (),
) -> tuple[Datacenter, ...]:
    """Return catalog DCs whose region is observed, plus required unassigned.

    ``require_unassigned_for`` lists region ids that need an unassigned DC
    because nodes/clusters exist without an explicit datacenter mapping.
    """

    region_ids = {r.id for r in regions}
    by_id: dict[str, Datacenter] = {}
    for dc in catalog:
        if dc.region_id in region_ids:
            by_id[dc.id] = dc
    region_by_id = {r.id: r for r in regions}
    for rid in require_unassigned_for:
        if rid not in region_ids:
            continue
        dc = unassigned_datacenter(region_by_id[rid])
        by_id.setdefault(dc.id, dc)
    return tuple(sorted(by_id.values(), key=lambda d: d.id))


def index_datacenters(
    datacenters: Sequence[Datacenter],
) -> Mapping[str, Datacenter]:
    return {d.id: d for d in datacenters}
