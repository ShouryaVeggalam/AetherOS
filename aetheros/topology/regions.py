"""Region catalog helpers — evidence-backed region definitions only.

Never invents regions that are not declared or observed on federation nodes.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from aetheros.topology.models import Region

# Well-known region labels → (display name, country). Used only when a
# federation node already reports that region id — not speculative.
KNOWN_REGIONS: Mapping[str, tuple[str, str]] = {
    "local": ("Local", "Local"),
    "us-west": ("US West", "United States"),
    "us-east": ("US East", "United States"),
    "eu-central": ("Europe Central", "Germany"),
    "eu-west": ("Europe West", "Ireland"),
    "asia-south": ("Asia South", "India"),
    "ap-south": ("Asia Pacific South", "India"),
}


def region_from_id(
    region_id: str,
    *,
    catalog: Mapping[str, Region] | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> Region:
    """Resolve a region from catalog or known map; requires non-empty id."""

    rid = region_id.strip().lower()
    if not rid:
        raise ValueError("region_id must be non-empty")
    if catalog and rid in catalog:
        return catalog[rid]
    if catalog and region_id in catalog:
        return catalog[region_id]
    name, country = KNOWN_REGIONS.get(rid, (region_id, "Unknown"))
    meta = dict(metadata or {})
    return Region(id=rid, name=name, country=country, metadata=meta)


def select_regions(
    region_ids: Sequence[str],
    *,
    catalog: Mapping[str, Region] | None = None,
) -> tuple[Region, ...]:
    """Build unique Region objects for observed region ids only."""

    seen: set[str] = set()
    out: list[Region] = []
    for raw in region_ids:
        rid = raw.strip().lower()
        if not rid or rid in seen:
            continue
        seen.add(rid)
        out.append(region_from_id(rid, catalog=catalog))
    return tuple(sorted(out, key=lambda r: r.id))
