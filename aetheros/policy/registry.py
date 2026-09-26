"""Policy Studio registry — create / enable / disable / archive / version.

Published policies are immutable. Edits create a new version.
Persists JSON under a local data directory. No remote execution.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from aetheros.policy.models import Policy, Rule


@dataclass
class PolicyRegistry:
    """Local versioned policy store.

    Args:
        root: Directory for ``policies.json``.
    """

    root: Path = field(default_factory=lambda: Path("data/policy_studio"))
    _versions: dict[str, list[Policy]] = field(default_factory=dict, init=False)
    _loaded: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    @property
    def store_path(self) -> Path:
        """JSON persistence path."""

        return self.root / "policies.json"

    def ensure_loaded(self) -> None:
        """Load versions from disk once."""

        if self._loaded:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self._versions = self._read()
        self._loaded = True

    def reload(self) -> None:
        """Force reload from disk."""

        self._loaded = False
        self.ensure_loaded()

    def create(
        self,
        *,
        id: str,
        name: str,
        description: str,
        rules: tuple[Rule, ...],
        priority: int = 10,
        enabled: bool = True,
        publish: bool = True,
    ) -> Policy:
        """Create version 1 of a new policy family."""

        self.ensure_loaded()
        if id in self._versions and self._versions[id]:
            raise ValueError(f"policy already exists: {id}")
        policy = Policy(
            id=id,
            name=name,
            description=description,
            priority=priority,
            enabled=enabled,
            created_at=datetime.now(UTC),
            version=1,
            status="published" if publish else "draft",
            rules=rules,
        )
        self._versions[id] = [policy]
        self._write()
        return policy

    def new_version(
        self,
        policy_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        rules: tuple[Rule, ...] | None = None,
        priority: int | None = None,
        enabled: bool | None = None,
        publish: bool = True,
    ) -> Policy:
        """Create a new immutable version from the latest head.

        Raises:
            KeyError: When the policy family does not exist.
            ValueError: When the latest version is not published/draft head.
        """

        self.ensure_loaded()
        history = self._versions.get(policy_id)
        if not history:
            raise KeyError(f"unknown policy: {policy_id}")
        head = history[-1]
        if head.status == "archived" and rules is None and name is None:
            # Allow resurrecting via new_version explicitly
            pass
        nxt = Policy(
            id=head.id,
            name=name if name is not None else head.name,
            description=description if description is not None else head.description,
            priority=priority if priority is not None else head.priority,
            enabled=enabled if enabled is not None else head.enabled,
            created_at=datetime.now(UTC),
            version=head.version + 1,
            status="published" if publish else "draft",
            rules=rules if rules is not None else head.rules,
        )
        history.append(nxt)
        self._write()
        return nxt

    def enable(self, policy_id: str) -> Policy:
        """Enable the latest version (new version flip — published immutability)."""

        return self._toggle(policy_id, enabled=True)

    def disable(self, policy_id: str) -> Policy:
        """Disable the latest version via a new published revision."""

        return self._toggle(policy_id, enabled=False)

    def archive(self, policy_id: str) -> Policy:
        """Archive the policy family by appending an archived version."""

        self.ensure_loaded()
        history = self._versions.get(policy_id)
        if not history:
            raise KeyError(f"unknown policy: {policy_id}")
        head = history[-1]
        archived = Policy(
            id=head.id,
            name=head.name,
            description=head.description,
            priority=head.priority,
            enabled=False,
            created_at=datetime.now(UTC),
            version=head.version + 1,
            status="archived",
            rules=head.rules,
        )
        history.append(archived)
        self._write()
        return archived

    def get_policy(
        self, policy_id: str, *, version: int | None = None
    ) -> Policy | None:
        """Return a policy head or a specific version."""

        self.ensure_loaded()
        history = self._versions.get(policy_id)
        if not history:
            return None
        if version is None:
            return history[-1]
        for item in history:
            if item.version == version:
                return item
        return None

    def list_policies(self, *, include_archived: bool = False) -> tuple[Policy, ...]:
        """Return latest heads, optionally including archived families."""

        self.ensure_loaded()
        heads: list[Policy] = []
        for policy_id in sorted(self._versions):
            head = self._versions[policy_id][-1]
            if head.status == "archived" and not include_archived:
                continue
            heads.append(head)
        return tuple(sorted(heads, key=lambda p: (-p.priority, p.id)))

    def versions(self, policy_id: str) -> tuple[Policy, ...]:
        """Return full version history for a policy family."""

        self.ensure_loaded()
        history = self._versions.get(policy_id) or []
        return tuple(history)

    def _toggle(self, policy_id: str, *, enabled: bool) -> Policy:
        self.ensure_loaded()
        history = self._versions.get(policy_id)
        if not history:
            raise KeyError(f"unknown policy: {policy_id}")
        head = history[-1]
        if head.status == "archived":
            raise ValueError(f"cannot enable/disable archived policy: {policy_id}")
        if head.enabled is enabled and head.status == "published":
            return head
        # Immutability: flip via new version
        return self.new_version(policy_id, enabled=enabled, publish=True)

    def _read(self) -> dict[str, list[Policy]]:
        if not self.store_path.is_file():
            return {}
        raw = json.loads(self.store_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        items = raw.get("policies") or []
        out: dict[str, list[Policy]] = {}
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                policy = Policy.from_dict(item)
                out.setdefault(policy.id, []).append(policy)
        for policy_id in out:
            out[policy_id].sort(key=lambda p: p.version)
        return out

    def _write(self) -> None:
        flat: list[dict[str, object]] = []
        for policy_id in sorted(self._versions):
            for policy in self._versions[policy_id]:
                flat.append(policy.to_dict())
        self.root.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(
            json.dumps({"policies": flat}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
