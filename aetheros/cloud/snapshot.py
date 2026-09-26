"""Immutable infrastructure snapshot engine.

capture() · serialize() · compare() · hash() — JSON only, never pickle.
Snapshots are frozen; compare returns structural diffs for operators.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from aetheros.cloud.models import (
    CloudProvider,
    CloudResource,
    InfrastructureSnapshot,
)
from aetheros.cloud.serializer import (
    decode_snapshot,
    dumps_canonical,
    encode_snapshot,
    snapshot_to_json,
)


@dataclass(frozen=True, slots=True)
class SnapshotDiff:
    """Structural comparison between two infrastructure snapshots."""

    added_providers: tuple[str, ...]
    removed_providers: tuple[str, ...]
    added_resources: tuple[str, ...]
    removed_resources: tuple[str, ...]
    hash_changed: bool

    @property
    def identical(self) -> bool:
        """True when topology hashes match and no membership changes."""

        return (
            not self.hash_changed
            and not self.added_providers
            and not self.removed_providers
            and not self.added_resources
            and not self.removed_resources
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON export."""

        return {
            "added_providers": list(self.added_providers),
            "removed_providers": list(self.removed_providers),
            "added_resources": list(self.added_resources),
            "removed_resources": list(self.removed_resources),
            "hash_changed": self.hash_changed,
            "identical": self.identical,
        }


def topology_hash(
    providers: tuple[CloudProvider, ...],
    resources: tuple[CloudResource, ...],
) -> str:
    """Content hash of provider ids + resource ids/types (sha256 hex)."""

    payload = {
        "providers": sorted(p.id for p in providers),
        "resources": sorted(f"{r.provider}:{r.type}:{r.id}" for r in resources),
    }
    digest = hashlib.sha256(dumps_canonical(payload).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def capture(
    providers: tuple[CloudProvider, ...] | list[CloudProvider],
    resources: tuple[CloudResource, ...] | list[CloudResource],
    *,
    timestamp: datetime | None = None,
) -> InfrastructureSnapshot:
    """Build an immutable infrastructure snapshot."""

    prov = tuple(providers)
    res = tuple(resources)
    moment = timestamp or datetime.now(UTC)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UTC)
    return InfrastructureSnapshot(
        timestamp=moment,
        providers=prov,
        resources=res,
        topology_hash=topology_hash(prov, res),
    )


def serialize(snapshot: InfrastructureSnapshot, *, pretty: bool = False) -> str:
    """Export snapshot as JSON text (never pickle)."""

    if pretty:
        return snapshot_to_json(snapshot, indent=2)
    return encode_snapshot(snapshot)


def deserialize(text: str) -> InfrastructureSnapshot:
    """Parse a snapshot from JSON text."""

    return decode_snapshot(text)


def compare(
    left: InfrastructureSnapshot,
    right: InfrastructureSnapshot,
) -> SnapshotDiff:
    """Diff two snapshots by provider/resource membership and hash."""

    left_p = {p.id for p in left.providers}
    right_p = {p.id for p in right.providers}
    left_r = {r.id for r in left.resources}
    right_r = {r.id for r in right.resources}
    return SnapshotDiff(
        added_providers=tuple(sorted(right_p - left_p)),
        removed_providers=tuple(sorted(left_p - right_p)),
        added_resources=tuple(sorted(right_r - left_r)),
        removed_resources=tuple(sorted(left_r - right_r)),
        hash_changed=left.topology_hash != right.topology_hash,
    )


def hash_snapshot(snapshot: InfrastructureSnapshot) -> str:
    """Return the snapshot topology hash (recomputed for verification)."""

    recomputed = topology_hash(snapshot.providers, snapshot.resources)
    return recomputed
