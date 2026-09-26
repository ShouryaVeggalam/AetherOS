"""Capability registration — plugins declare what they may touch.

Capabilities are advisory grants checked by the validator / loader.
They never elevate privileges beyond the sandboxed read-only API.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from plugins.sdk.version import SUPPORTED_CAPABILITIES


@dataclass(frozen=True, slots=True)
class CapabilityGrant:
    """One granted capability with optional scope note."""

    name: str
    scope: str = "*"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("capability name must be non-empty")


@dataclass
class CapabilityRegistry:
    """Mutable registry of grants for one loaded plugin session."""

    _grants: list[CapabilityGrant] = field(default_factory=list)

    def register(self, name: str, *, scope: str = "*") -> CapabilityGrant:
        """Register a capability if the SDK supports it."""

        key = name.strip()
        if key not in SUPPORTED_CAPABILITIES:
            raise ValueError(f"unsupported capability: {name}")
        grant = CapabilityGrant(name=key, scope=scope)
        self._grants.append(grant)
        return grant

    def register_many(self, names: Iterable[str]) -> tuple[CapabilityGrant, ...]:
        """Register multiple capability names with default scope."""

        return tuple(self.register(name) for name in names)

    def has(self, name: str) -> bool:
        """Return True when ``name`` was granted."""

        return any(g.name == name for g in self._grants)

    def grants(self) -> tuple[CapabilityGrant, ...]:
        """Return all grants in registration order."""

        return tuple(self._grants)

    def require(self, name: str) -> None:
        """Raise ``PermissionError`` when a capability was not granted."""

        if not self.has(name):
            raise PermissionError(f"capability not granted: {name}")
