"""Enterprise organizations — create / list / get metadata only.

Writes organization records + audit events. Never touches core intelligence.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from aetheros.enterprise.audit import AuditLog
from aetheros.enterprise.models import Organization


@dataclass
class OrganizationService:
    """Local JSON-backed organization registry.

    Args:
        root: Data directory for ``organizations.json``.
        audit: Append-only audit log.
    """

    root: Path = field(default_factory=lambda: Path("data/enterprise"))
    audit: AuditLog | None = None
    _orgs: dict[str, Organization] = field(default_factory=dict, init=False)
    _loaded: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    @property
    def store_path(self) -> Path:
        """Path to organizations JSON index."""

        return self.root / "organizations.json"

    def ensure_loaded(self) -> None:
        """Load organizations from disk once."""

        if self._loaded:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self._orgs = self._read()
        self._loaded = True

    def create(self, name: str, *, actor: str = "system") -> Organization:
        """Create a new organization and emit an audit event."""

        self.ensure_loaded()
        org = Organization(
            id=f"org-{uuid.uuid4().hex[:10]}",
            name=name.strip(),
            created_at=datetime.now(UTC),
        )
        self._orgs[org.id] = org
        self._write()
        self._emit(actor, "Organization Created", org.id, {"name": org.name})
        return org

    def get(self, organization_id: str) -> Organization | None:
        """Return one organization or None."""

        self.ensure_loaded()
        return self._orgs.get(organization_id)

    def list(self) -> tuple[Organization, ...]:
        """Return all organizations (immutable, sorted by name)."""

        self.ensure_loaded()
        return tuple(sorted(self._orgs.values(), key=lambda o: o.name.lower()))

    def _emit(
        self, actor: str, action: str, resource: str, metadata: dict[str, str]
    ) -> None:
        if self.audit is not None:
            self.audit.append(
                actor=actor,
                action=action,
                resource=resource,
                metadata=metadata,
            )

    def _read(self) -> dict[str, Organization]:
        if not self.store_path.is_file():
            return {}
        raw = json.loads(self.store_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        items = raw.get("organizations") or []
        out: dict[str, Organization] = {}
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    org = Organization.from_dict(item)
                    out[org.id] = org
        return out

    def _write(self) -> None:
        payload = {
            "organizations": [self._orgs[k].to_dict() for k in sorted(self._orgs)]
        }
        self.root.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
