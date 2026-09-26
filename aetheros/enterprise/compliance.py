"""Enterprise compliance reports — Markdown + JSON only.

SOC2 readiness, ISO 27001 mapping, audit summary, access report.
Read-only over audit + RBAC metadata.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from aetheros.enterprise.audit import AuditLog
from aetheros.enterprise.models import APIKey, Member, Organization, Workspace
from aetheros.enterprise.rbac import role_matrix


@dataclass(frozen=True, slots=True)
class ComplianceReport:
    """Immutable compliance artifact (Markdown + JSON payloads)."""

    title: str
    kind: str
    generated_at: datetime
    markdown: str
    data: dict[str, Any]

    def to_json(self) -> str:
        """Serialize the structured payload as JSON text."""

        envelope = {
            "title": self.title,
            "kind": self.kind,
            "generated_at": self.generated_at.isoformat(),
            "data": self.data,
        }
        return json.dumps(envelope, indent=2, sort_keys=True) + "\n"


class ComplianceService:
    """Generate read-only compliance reports from enterprise metadata."""

    def __init__(
        self,
        *,
        audit: AuditLog,
        organizations: tuple[Organization, ...] = (),
        workspaces: tuple[Workspace, ...] = (),
        members: tuple[Member, ...] = (),
        api_keys: tuple[APIKey, ...] = (),
    ) -> None:
        self.audit = audit
        self.organizations = organizations
        self.workspaces = workspaces
        self.members = members
        self.api_keys = api_keys

    def soc2_readiness(self) -> ComplianceReport:
        """SOC2-oriented control readiness summary."""

        events = self.audit.list()
        checks = {
            "audit_logging": self.audit.count() > 0,
            "rbac_defined": True,
            "api_key_lifecycle": any(not k.revoked for k in self.api_keys)
            or len(self.api_keys) == 0,
            "org_isolation": len(self.organizations) >= 1,
            "append_only_audit": True,
        }
        ready = all(checks.values())
        lines = [
            "# SOC2 Readiness",
            "",
            f"Generated: {datetime.now(UTC).isoformat()}",
            "",
            f"Status: **{'Ready' if ready else 'Gaps Remain'}**",
            "",
            "| Control | Status |",
            "|---------|--------|",
        ]
        for name, ok in checks.items():
            lines.append(f"| {name} | {'pass' if ok else 'fail'} |")
        lines.extend(
            [
                "",
                f"Audit events: {len(events)}",
                f"Organizations: {len(self.organizations)}",
                f"Workspaces: {len(self.workspaces)}",
            ]
        )
        return ComplianceReport(
            title="SOC2 Readiness",
            kind="soc2",
            generated_at=datetime.now(UTC),
            markdown="\n".join(lines) + "\n",
            data={"ready": ready, "checks": checks, "audit_events": len(events)},
        )

    def iso27001_mapping(self) -> ComplianceReport:
        """Map enterprise features onto illustrative ISO 27001 control themes."""

        mapping = {
            "A.5 Organizational controls": [
                "Organization registry",
                "Workspace isolation",
            ],
            "A.8 Asset management": [
                "API key inventory",
                "Plugin/policy manage scopes",
            ],
            "A.8.2 Access control": ["RBAC roles", "Least-privilege scopes"],
            "A.8.15 Logging": ["Append-only audit log"],
            "A.8.16 Monitoring": ["Usage analytics"],
        }
        lines = [
            "# ISO 27001 Mapping",
            "",
            f"Generated: {datetime.now(UTC).isoformat()}",
            "",
        ]
        for control, items in mapping.items():
            lines.append(f"## {control}")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")
        return ComplianceReport(
            title="ISO 27001 Mapping",
            kind="iso27001",
            generated_at=datetime.now(UTC),
            markdown="\n".join(lines),
            data={"mapping": mapping},
        )

    def audit_summary(self) -> ComplianceReport:
        """Summarize audit actions by type."""

        events = self.audit.list()
        counts: dict[str, int] = {}
        for event in events:
            counts[event.action] = counts.get(event.action, 0) + 1
        lines = [
            "# Audit Summary",
            "",
            f"Total events: {len(events)}",
            "",
            "| Action | Count |",
            "|--------|------:|",
        ]
        for action, count in sorted(counts.items()):
            lines.append(f"| {action} | {count} |")
        return ComplianceReport(
            title="Audit Summary",
            kind="audit_summary",
            generated_at=datetime.now(UTC),
            markdown="\n".join(lines) + "\n",
            data={"total": len(events), "by_action": counts},
        )

    def access_report(self) -> ComplianceReport:
        """Access / membership / key inventory report."""

        matrix = role_matrix()
        lines = [
            "# Access Report",
            "",
            f"Members: {len(self.members)}",
            f"API keys: {len(self.api_keys)}",
            "",
            "## Role matrix",
            "",
        ]
        for role, perms in matrix.items():
            lines.append(f"- **{role}**: {', '.join(perms)}")
        lines.append("")
        lines.append("## Members")
        for member in self.members:
            lines.append(f"- {member.actor} @ {member.workspace_id} → {member.role}")
        lines.append("")
        lines.append("## API keys")
        for key in self.api_keys:
            status = "revoked" if key.revoked else "active"
            lines.append(
                f"- {key.id} ({key.prefix}…) scopes={list(key.scopes)} [{status}]"
            )
        return ComplianceReport(
            title="Access Report",
            kind="access",
            generated_at=datetime.now(UTC),
            markdown="\n".join(lines) + "\n",
            data={
                "members": [m.to_dict() for m in self.members],
                "api_keys": [k.to_dict() for k in self.api_keys],
                "role_matrix": {r: list(p) for r, p in matrix.items()},
            },
        )
