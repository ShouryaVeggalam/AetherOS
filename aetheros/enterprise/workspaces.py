"""Enterprise workspaces — create / list / membership metadata.

Writes workspace + member records and audit events only.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from aetheros.enterprise.audit import AuditLog
from aetheros.enterprise.models import VIEWER, Member, Workspace


@dataclass
class WorkspaceService:
    """Local JSON-backed workspace + membership registry.

    Args:
        root: Data directory for workspace JSON files.
        audit: Append-only audit log.
    """

    root: Path = field(default_factory=lambda: Path("data/enterprise"))
    audit: AuditLog | None = None
    _workspaces: dict[str, Workspace] = field(default_factory=dict, init=False)
    _members: dict[str, Member] = field(default_factory=dict, init=False)
    _loaded: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    @property
    def store_path(self) -> Path:
        """Path to workspaces JSON index."""

        return self.root / "workspaces.json"

    def ensure_loaded(self) -> None:
        """Load workspaces + members from disk once."""

        if self._loaded:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self._workspaces, self._members = self._read()
        self._loaded = True

    def create(
        self,
        organization_id: str,
        name: str,
        *,
        actor: str = "system",
    ) -> Workspace:
        """Create a workspace under ``organization_id``."""

        self.ensure_loaded()
        if not organization_id.strip():
            raise ValueError("organization_id required")
        ws = Workspace(
            id=f"ws-{uuid.uuid4().hex[:10]}",
            organization_id=organization_id.strip(),
            name=name.strip(),
        )
        self._workspaces[ws.id] = ws
        self._write()
        self._emit(
            actor,
            "Workspace Created",
            ws.id,
            {"name": ws.name, "organization_id": ws.organization_id},
        )
        return ws

    def get(self, workspace_id: str) -> Workspace | None:
        """Return one workspace or None."""

        self.ensure_loaded()
        return self._workspaces.get(workspace_id)

    def list(self, *, organization_id: str | None = None) -> tuple[Workspace, ...]:
        """Return workspaces, optionally filtered by organization."""

        self.ensure_loaded()
        items = list(self._workspaces.values())
        if organization_id is not None:
            items = [w for w in items if w.organization_id == organization_id]
        return tuple(sorted(items, key=lambda w: w.name.lower()))

    def add_member(
        self,
        workspace_id: str,
        actor: str,
        role: str = VIEWER,
        *,
        performed_by: str = "system",
    ) -> Member:
        """Add a member with least-privilege default role VIEWER."""

        self.ensure_loaded()
        if workspace_id not in self._workspaces:
            raise KeyError(f"unknown workspace: {workspace_id}")
        member = Member(
            id=f"mem-{uuid.uuid4().hex[:10]}",
            workspace_id=workspace_id,
            actor=actor.strip(),
            role=role.strip().upper(),
        )
        self._members[member.id] = member
        self._write()
        self._emit(
            performed_by,
            "Member Added",
            member.id,
            {
                "workspace_id": workspace_id,
                "actor": member.actor,
                "role": member.role,
            },
        )
        return member

    def list_members(self, workspace_id: str) -> tuple[Member, ...]:
        """Return members for one workspace."""

        self.ensure_loaded()
        return tuple(
            m
            for m in sorted(self._members.values(), key=lambda x: x.actor.lower())
            if m.workspace_id == workspace_id
        )

    def member_count(self, *, organization_id: str | None = None) -> int:
        """Count members, optionally scoped to an organization's workspaces."""

        self.ensure_loaded()
        if organization_id is None:
            return len(self._members)
        ws_ids = {
            w.id
            for w in self._workspaces.values()
            if w.organization_id == organization_id
        }
        return sum(1 for m in self._members.values() if m.workspace_id in ws_ids)

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

    def _read(self) -> tuple[dict[str, Workspace], dict[str, Member]]:
        if not self.store_path.is_file():
            return {}, {}
        raw = json.loads(self.store_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}, {}
        workspaces: dict[str, Workspace] = {}
        members: dict[str, Member] = {}
        for item in raw.get("workspaces") or []:
            if isinstance(item, dict):
                ws = Workspace.from_dict(item)
                workspaces[ws.id] = ws
        for item in raw.get("members") or []:
            if isinstance(item, dict):
                mem = Member.from_dict(item)
                members[mem.id] = mem
        return workspaces, members

    def _write(self) -> None:
        payload = {
            "workspaces": [
                self._workspaces[k].to_dict() for k in sorted(self._workspaces)
            ],
            "members": [self._members[k].to_dict() for k in sorted(self._members)],
        }
        self.root.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
