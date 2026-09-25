"""Fabric protocol versioning — schema and agent version stamps.

Immutable version records enable eventual-consistency reconciliation
without remote execution.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProtocolVersion:
    """One immutable protocol / fabric version stamp.

    Attributes:
        major: Incompatible wire changes.
        minor: Backward-compatible additions.
        patch: Fixes / clarifications.
        label: Human label (e.g. ``aether-fabric``).
    """

    major: int
    minor: int
    patch: int
    label: str = "aether-fabric"

    def __post_init__(self) -> None:
        """Reject negative components."""

        if min(self.major, self.minor, self.patch) < 0:
            raise ValueError("version components must be >= 0")

    def __str__(self) -> str:
        """Return ``label/major.minor.patch``."""

        return f"{self.label}/{self.major}.{self.minor}.{self.patch}"

    def compatible_with(self, other: ProtocolVersion) -> bool:
        """True when major versions match (minor/patch may drift)."""

        return self.major == other.major and self.label == other.label


FABRIC_PROTOCOL = ProtocolVersion(1, 0, 0, "aether-fabric")
