"""Enterprise audit log — append-only, never deletable.

Every enterprise action should emit an AuditEvent. Deletion APIs are absent.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from aetheros.enterprise.models import AuditEvent


@dataclass
class AuditLog:
    """Append-only JSONL audit store.

    Args:
        root: Directory holding ``audit.jsonl``.
    """

    root: Path = field(default_factory=lambda: Path("data/enterprise"))
    _events: list[AuditEvent] = field(default_factory=list, init=False)
    _loaded: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    @property
    def path(self) -> Path:
        """Path to the append-only JSONL file."""

        return self.root / "audit.jsonl"

    def ensure_loaded(self) -> None:
        """Load existing events from disk once."""

        if self._loaded:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self._events = self._read()
        self._loaded = True

    def append(
        self,
        *,
        actor: str,
        action: str,
        resource: str,
        metadata: Mapping[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> AuditEvent:
        """Append one immutable audit event (never overwrites history)."""

        self.ensure_loaded()
        event = AuditEvent(
            id=f"aud-{uuid.uuid4().hex[:12]}",
            actor=actor.strip(),
            action=action.strip(),
            resource=resource.strip(),
            timestamp=timestamp or datetime.now(UTC),
            metadata=tuple(
                sorted((str(k), str(v)) for k, v in (metadata or {}).items())
            ),
        )
        self.root.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
        self._events.append(event)
        return event

    def list(
        self,
        *,
        action: str | None = None,
        actor: str | None = None,
        limit: int | None = None,
    ) -> tuple[AuditEvent, ...]:
        """Return audit events (oldest → newest), optionally filtered."""

        self.ensure_loaded()
        items = list(self._events)
        if action is not None:
            items = [e for e in items if e.action == action]
        if actor is not None:
            items = [e for e in items if e.actor == actor]
        if limit is not None:
            items = items[-limit:]
        return tuple(items)

    def count(self) -> int:
        """Return total audit event count."""

        self.ensure_loaded()
        return len(self._events)

    def _read(self) -> list[AuditEvent]:
        if not self.path.is_file():
            return []
        events: list[AuditEvent] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(raw, dict):
                events.append(AuditEvent.from_dict(raw))
        return events
