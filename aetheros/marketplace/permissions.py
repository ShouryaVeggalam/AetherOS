"""Marketplace permission model — read-only grants only.

Maps marketplace permission names onto Plugin SDK capabilities.
Never allows WRITE permissions. Sandbox-by-default policy.
"""

from __future__ import annotations

from collections.abc import Iterable

# Marketplace-facing permission names (uppercase, discoverable).
READ_GRAPH = "READ_GRAPH"
READ_CONTEXT = "READ_CONTEXT"
READ_TELEMETRY = "READ_TELEMETRY"
READ_RESEARCH = "READ_RESEARCH"
READ_SIMULATION = "READ_SIMULATION"

ALLOWED_PERMISSIONS: frozenset[str] = frozenset(
    {
        READ_GRAPH,
        READ_CONTEXT,
        READ_TELEMETRY,
        READ_RESEARCH,
        READ_SIMULATION,
    }
)

# Bridge to plugins.sdk capability strings (when loading via Plugin SDK).
PERMISSION_TO_CAPABILITY: dict[str, str] = {
    READ_GRAPH: "graph.read",
    READ_CONTEXT: "context.read",
    READ_TELEMETRY: "telemetry.read",
    READ_RESEARCH: "learning.analyze",
    READ_SIMULATION: "simulation.model",
}


def normalize_permission(name: str) -> str:
    """Normalize a permission token to the marketplace uppercase form."""

    text = name.strip()
    if not text:
        return ""
    # Accept SDK-style dotted names as aliases.
    for perm, capability in PERMISSION_TO_CAPABILITY.items():
        if text == capability or text.upper() == perm:
            return perm
    return text.upper().replace(".", "_")


def is_write_permission(name: str) -> bool:
    """Return True when a permission token implies mutation."""

    token = name.strip().upper().replace(".", "_")
    return (
        token.startswith("WRITE_")
        or token.endswith("_WRITE")
        or "WRITE" in token.split("_")
    )


def validate_permissions(permissions: Iterable[str]) -> tuple[str, ...]:
    """Validate and normalize permissions.

    Returns:
        Sorted unique allowed permission names.

    Raises:
        ValueError: On empty tokens, WRITE grants, or unsupported names.
    """

    accepted: set[str] = set()
    for raw in permissions:
        if not str(raw).strip():
            raise ValueError("permission tokens must be non-empty")
        if is_write_permission(str(raw)):
            raise ValueError(f"WRITE permissions are never allowed: {raw!r}")
        normalized = normalize_permission(str(raw))
        if normalized not in ALLOWED_PERMISSIONS:
            raise ValueError(f"unsupported permission: {raw!r}")
        accepted.add(normalized)
    return tuple(sorted(accepted))


def to_sdk_capabilities(permissions: Iterable[str]) -> tuple[str, ...]:
    """Map marketplace permissions onto Plugin SDK capability strings."""

    validated = validate_permissions(permissions)
    return tuple(PERMISSION_TO_CAPABILITY[p] for p in validated)
