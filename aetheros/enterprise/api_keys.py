"""Enterprise API keys — create / revoke / rotate / validate.

Scopes are immutable after creation. Raw secrets are returned once at
create/rotate time and never persisted or re-exposed.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from aetheros.enterprise.audit import AuditLog
from aetheros.enterprise.models import APIKey
from aetheros.enterprise.rbac import validate_scopes


def _hash_secret(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def _mint_secret() -> tuple[str, str, str]:
    """Return ``(raw_secret, key_hash, prefix)``."""

    raw = f"aether_{secrets.token_urlsafe(32)}"
    return raw, _hash_secret(raw), raw[:12]


@dataclass(frozen=True, slots=True)
class IssuedAPIKey:
    """One-time issuance envelope (raw secret shown only here)."""

    key: APIKey
    secret: str


@dataclass
class APIKeyService:
    """Local JSON-backed API key metadata store.

    Args:
        root: Data directory for ``api_keys.json``.
        audit: Append-only audit log.
    """

    root: Path = field(default_factory=lambda: Path("data/enterprise"))
    audit: AuditLog | None = None
    _keys: dict[str, APIKey] = field(default_factory=dict, init=False)
    _loaded: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    @property
    def store_path(self) -> Path:
        """Path to API key metadata JSON."""

        return self.root / "api_keys.json"

    def ensure_loaded(self) -> None:
        """Load key metadata from disk once."""

        if self._loaded:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self._keys = self._read()
        self._loaded = True

    def create(
        self,
        workspace_id: str,
        scopes: tuple[str, ...] | list[str],
        *,
        actor: str = "system",
        label: str = "",
        ttl_days: int | None = 365,
    ) -> IssuedAPIKey:
        """Create a key; returns metadata + raw secret (shown once)."""

        self.ensure_loaded()
        validated = validate_scopes(scopes)
        raw, digest, prefix = _mint_secret()
        now = datetime.now(UTC)
        expires = now + timedelta(days=ttl_days) if ttl_days else None
        record = APIKey(
            id=f"key-{uuid.uuid4().hex[:10]}",
            workspace_id=workspace_id.strip(),
            scopes=validated,
            created_at=now,
            expires_at=expires,
            key_hash=digest,
            prefix=prefix,
            revoked=False,
            label=label.strip(),
        )
        self._keys[record.id] = record
        self._write()
        self._emit(
            actor,
            "API Key Created",
            record.id,
            {"workspace_id": workspace_id, "prefix": prefix},
        )
        return IssuedAPIKey(key=record, secret=raw)

    def revoke(self, key_id: str, *, actor: str = "system") -> APIKey:
        """Revoke a key (immutable scopes preserved; revoked flag set)."""

        self.ensure_loaded()
        current = self._keys.get(key_id)
        if current is None:
            raise KeyError(f"unknown api key: {key_id}")
        if current.revoked:
            return current
        updated = APIKey(
            id=current.id,
            workspace_id=current.workspace_id,
            scopes=current.scopes,
            created_at=current.created_at,
            expires_at=current.expires_at,
            key_hash=current.key_hash,
            prefix=current.prefix,
            revoked=True,
            label=current.label,
        )
        self._keys[key_id] = updated
        self._write()
        self._emit(actor, "API Key Revoked", key_id, {"prefix": updated.prefix})
        return updated

    def rotate(
        self,
        key_id: str,
        *,
        actor: str = "system",
        ttl_days: int | None = 365,
    ) -> IssuedAPIKey:
        """Revoke ``key_id`` and issue a replacement with the same scopes."""

        self.ensure_loaded()
        current = self._keys.get(key_id)
        if current is None:
            raise KeyError(f"unknown api key: {key_id}")
        self.revoke(key_id, actor=actor)
        issued = self.create(
            current.workspace_id,
            current.scopes,
            actor=actor,
            label=current.label or f"rotated-from-{key_id}",
            ttl_days=ttl_days,
        )
        self._emit(
            actor,
            "API Key Rotated",
            issued.key.id,
            {"previous": key_id, "prefix": issued.key.prefix},
        )
        return issued

    def validate(self, secret: str) -> APIKey | None:
        """Validate a raw secret; returns metadata when active and unexpired."""

        self.ensure_loaded()
        digest = _hash_secret(secret)
        now = datetime.now(UTC)
        for record in self._keys.values():
            if record.key_hash != digest:
                continue
            if record.revoked:
                return None
            if record.expires_at is not None and record.expires_at <= now:
                return None
            return record
        return None

    def get(self, key_id: str) -> APIKey | None:
        """Return key metadata (never the raw secret)."""

        self.ensure_loaded()
        return self._keys.get(key_id)

    def list(self, *, workspace_id: str | None = None) -> tuple[APIKey, ...]:
        """List key metadata records."""

        self.ensure_loaded()
        items = list(self._keys.values())
        if workspace_id is not None:
            items = [k for k in items if k.workspace_id == workspace_id]
        return tuple(sorted(items, key=lambda k: k.created_at))

    def _emit(
        self, actor: str, action: str, resource: str, metadata: dict[str, str]
    ) -> None:
        if self.audit is not None:
            self.audit.append(
                actor=actor, action=action, resource=resource, metadata=metadata
            )

    def _read(self) -> dict[str, APIKey]:
        if not self.store_path.is_file():
            return {}
        raw = json.loads(self.store_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        out: dict[str, APIKey] = {}
        for item in raw.get("api_keys") or []:
            if isinstance(item, dict):
                key = APIKey.from_dict(item)
                out[key.id] = key
        return out

    def _write(self) -> None:
        payload = {"api_keys": [self._keys[k].to_dict() for k in sorted(self._keys)]}
        self.root.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
