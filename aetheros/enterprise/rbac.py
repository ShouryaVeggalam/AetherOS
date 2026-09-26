"""Enterprise RBAC — least-privilege role → permission grants.

No wildcard permissions. VIEWER is the default (read-only subset).
"""

from __future__ import annotations

from collections.abc import Iterable

from aetheros.enterprise.models import ADMIN, ANALYST, ENGINEER, ROLES, VIEWER

# Explicit permission vocabulary (no wildcards).
READ_GRAPH = "READ_GRAPH"
READ_CONTEXT = "READ_CONTEXT"
READ_REASONING = "READ_REASONING"
READ_RESEARCH = "READ_RESEARCH"
READ_SIMULATION = "READ_SIMULATION"
MANAGE_PLUGINS = "MANAGE_PLUGINS"
MANAGE_POLICIES = "MANAGE_POLICIES"

ALL_PERMISSIONS: frozenset[str] = frozenset(
    {
        READ_GRAPH,
        READ_CONTEXT,
        READ_REASONING,
        READ_RESEARCH,
        READ_SIMULATION,
        MANAGE_PLUGINS,
        MANAGE_POLICIES,
    }
)

# Least privilege: VIEWER ⊂ ANALYST ⊂ ENGINEER ⊂ ADMIN
_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    VIEWER: frozenset(
        {
            READ_GRAPH,
            READ_CONTEXT,
        }
    ),
    ANALYST: frozenset(
        {
            READ_GRAPH,
            READ_CONTEXT,
            READ_REASONING,
            READ_RESEARCH,
            READ_SIMULATION,
        }
    ),
    ENGINEER: frozenset(
        {
            READ_GRAPH,
            READ_CONTEXT,
            READ_REASONING,
            READ_RESEARCH,
            READ_SIMULATION,
            MANAGE_PLUGINS,
        }
    ),
    ADMIN: frozenset(ALL_PERMISSIONS),
}


def permissions_for(role: str) -> frozenset[str]:
    """Return the immutable permission set for ``role``."""

    key = role.strip().upper()
    if key not in ROLES:
        raise ValueError(f"unknown role: {role!r}")
    return _ROLE_PERMISSIONS[key]


def has_permission(role: str, permission: str) -> bool:
    """Return True when ``role`` includes ``permission``."""

    if permission not in ALL_PERMISSIONS:
        raise ValueError(f"unknown permission: {permission!r}")
    return permission in permissions_for(role)


def require_permission(role: str, permission: str) -> None:
    """Raise ``PermissionError`` when the role lacks ``permission``."""

    if not has_permission(role, permission):
        raise PermissionError(f"role {role!r} lacks {permission}")


def validate_scopes(scopes: Iterable[str]) -> tuple[str, ...]:
    """Validate API key / grant scopes against the RBAC vocabulary.

    Raises:
        ValueError: On empty tokens, wildcards, or unknown permissions.
    """

    accepted: set[str] = set()
    for raw in scopes:
        token = str(raw).strip().upper()
        if not token:
            raise ValueError("scope tokens must be non-empty")
        if "*" in token or token == "ALL":
            raise ValueError("wildcard scopes are never allowed")
        if token not in ALL_PERMISSIONS:
            raise ValueError(f"unknown scope: {raw!r}")
        accepted.add(token)
    if not accepted:
        raise ValueError("scopes must be non-empty")
    return tuple(sorted(accepted))


def role_matrix() -> dict[str, tuple[str, ...]]:
    """Return a sorted role → permissions mapping for docs / UI."""

    return {
        role: tuple(sorted(_ROLE_PERMISSIONS[role]))
        for role in (VIEWER, ANALYST, ENGINEER, ADMIN)
    }
