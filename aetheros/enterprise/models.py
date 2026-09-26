"""Enterprise Edition models — immutable org / workspace / RBAC metadata.

Governance wrappers only. Never mutate Resource Graph, Reasoning, Twin,
Scheduler, Consensus, or core runtime behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

# Role names (uppercase tokens).
ADMIN = "ADMIN"
ENGINEER = "ENGINEER"
ANALYST = "ANALYST"
VIEWER = "VIEWER"

ROLES: frozenset[str] = frozenset({ADMIN, ENGINEER, ANALYST, VIEWER})


@dataclass(frozen=True, slots=True)
class Organization:
    """Enterprise organization (tenant) metadata."""

    id: str
    name: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON persistence."""

        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Organization:
        """Parse an Organization from a mapping."""

        return cls(
            id=str(data.get("id") or "").strip(),
            name=str(data.get("name") or "").strip(),
            created_at=datetime.fromisoformat(str(data.get("created_at") or "")),
        )


@dataclass(frozen=True, slots=True)
class Workspace:
    """Workspace scoped to one organization."""

    id: str
    organization_id: str
    name: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.organization_id.strip():
            raise ValueError("organization_id must be non-empty")
        if not self.name.strip():
            raise ValueError("name must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON persistence."""

        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Workspace:
        """Parse a Workspace from a mapping."""

        return cls(
            id=str(data.get("id") or "").strip(),
            organization_id=str(data.get("organization_id") or "").strip(),
            name=str(data.get("name") or "").strip(),
        )


@dataclass(frozen=True, slots=True)
class Member:
    """Workspace membership with a single Role (least privilege)."""

    id: str
    workspace_id: str
    actor: str
    role: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if self.role not in ROLES:
            raise ValueError(f"invalid role: {self.role!r}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON persistence."""

        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "actor": self.actor,
            "role": self.role,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Member:
        """Parse a Member from a mapping."""

        return cls(
            id=str(data.get("id") or "").strip(),
            workspace_id=str(data.get("workspace_id") or "").strip(),
            actor=str(data.get("actor") or "").strip(),
            role=str(data.get("role") or VIEWER).strip().upper(),
        )


@dataclass(frozen=True, slots=True)
class APIKey:
    """API key metadata — never stores the raw secret after creation."""

    id: str
    workspace_id: str
    scopes: tuple[str, ...]
    created_at: datetime
    expires_at: datetime | None
    key_hash: str
    prefix: str
    revoked: bool = False
    label: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id must be non-empty")
        if not self.workspace_id.strip():
            raise ValueError("workspace_id must be non-empty")
        if not self.key_hash.strip():
            raise ValueError("key_hash must be non-empty")
        if not self.scopes:
            raise ValueError("scopes must be non-empty")

    @property
    def workspace(self) -> str:
        """Alias for ``workspace_id`` (spec field name)."""

        return self.workspace_id

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata (never includes the raw secret)."""

        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "scopes": list(self.scopes),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "key_hash": self.key_hash,
            "prefix": self.prefix,
            "revoked": self.revoked,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> APIKey:
        """Parse API key metadata from a mapping."""

        scopes = data.get("scopes") or ()
        if isinstance(scopes, str):
            scopes = [scopes]
        expires = data.get("expires_at")
        return cls(
            id=str(data.get("id") or "").strip(),
            workspace_id=str(
                data.get("workspace_id") or data.get("workspace") or ""
            ).strip(),
            scopes=tuple(str(s).strip() for s in scopes if str(s).strip()),
            created_at=datetime.fromisoformat(str(data.get("created_at") or "")),
            expires_at=(datetime.fromisoformat(str(expires)) if expires else None),
            key_hash=str(data.get("key_hash") or "").strip(),
            prefix=str(data.get("prefix") or "").strip(),
            revoked=bool(data.get("revoked", False)),
            label=str(data.get("label") or "").strip(),
        )


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Append-only enterprise audit event (immutable, never deletable)."""

    actor: str
    action: str
    resource: str
    timestamp: datetime
    metadata: tuple[tuple[str, str], ...] = ()
    id: str = ""

    def __post_init__(self) -> None:
        if not self.actor.strip():
            raise ValueError("actor must be non-empty")
        if not self.action.strip():
            raise ValueError("action must be non-empty")
        if not self.resource.strip():
            raise ValueError("resource must be non-empty")

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON / Markdown reports."""

        return {
            "id": self.id,
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "timestamp": self.timestamp.isoformat(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditEvent:
        """Parse an AuditEvent from a mapping."""

        meta = data.get("metadata") or {}
        if isinstance(meta, dict):
            pairs = tuple((str(k), str(v)) for k, v in sorted(meta.items()))
        else:
            pairs = ()
        return cls(
            actor=str(data.get("actor") or "").strip(),
            action=str(data.get("action") or "").strip(),
            resource=str(data.get("resource") or "").strip(),
            timestamp=datetime.fromisoformat(str(data.get("timestamp") or "")),
            metadata=pairs,
            id=str(data.get("id") or "").strip(),
        )
