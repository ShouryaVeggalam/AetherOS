"""Rich formatter for Enterprise Edition dashboard panel (shortcut E).

@ remains Extensions (marketplace). E opens Enterprise governance views.
"""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.text import Text

from aetheros.enterprise.analytics import UsageMetrics
from aetheros.enterprise.models import (
    APIKey,
    AuditEvent,
    Member,
    Organization,
    Workspace,
)
from aetheros.enterprise.rbac import role_matrix


@dataclass(frozen=True, slots=True)
class EnterprisePanel:
    """Center-panel renderable for Enterprise Edition (shortcut E)."""

    organization: Organization | None = None
    workspaces: tuple[Workspace, ...] = ()
    members: tuple[Member, ...] = ()
    api_keys: tuple[APIKey, ...] = ()
    audit_events: tuple[AuditEvent, ...] = ()
    audit_count: int = 0
    compliance_status: str = "SOC2 Ready"
    metrics: UsageMetrics | None = None
    view: str = "organizations"

    def __rich__(self) -> RenderableType:
        if self.organization is None and not self.workspaces:
            return Panel(
                Text(
                    "ENTERPRISE idle.\n"
                    "Organizations · workspaces · RBAC · API keys · audit.\n"
                    "Governance wrappers only — core runtime unchanged.\n"
                    "E opens this page · @ remains Extensions.\n"
                    "Status: Read-only metadata",
                    style="dim",
                ),
                title="Enterprise Edition",
                border_style="bright_white",
            )

        view = self.view.lower()
        if view in {"workspaces", "workspace"}:
            body = self._workspaces_view()
        elif view in {"roles", "rbac"}:
            body = self._roles_view()
        elif view in {"keys", "api keys", "api_keys"}:
            body = self._keys_view()
        elif view == "audit":
            body = self._audit_view()
        elif view == "compliance":
            body = self._compliance_view()
        elif view == "analytics":
            body = self._analytics_view()
        else:
            body = self._organizations_view()
        return Panel(body, title="Enterprise Edition", border_style="bright_white")

    def _organizations_view(self) -> RenderableType:
        org_name = self.organization.name if self.organization else "—"
        parts: list[Text] = [
            Text("ENTERPRISE", style="bold bright_white"),
            Text(""),
            Text("Organization", style="bold"),
            Text(f"  {org_name}"),
            Text(""),
            Text("Workspaces", style="bold"),
            Text(f"  {len(self.workspaces)}"),
            Text(""),
            Text("Members", style="bold"),
            Text(f"  {len(self.members)}"),
            Text(""),
            Text("API Keys", style="bold"),
            Text(f"  {len(self.api_keys)}"),
            Text(""),
            Text("Audit Events", style="bold"),
            Text(f"  {self.audit_count:,}"),
            Text(""),
            Text("Compliance", style="bold"),
            Text(f"  {self.compliance_status}"),
            Text(""),
            Text("Status", style="bold"),
            Text("  Healthy"),
            Text(""),
            Text("View", style="dim"),
            Text("  Organizations  (] cycles)"),
        ]
        return Group(*parts)

    def _workspaces_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("ENTERPRISE", style="bold bright_white"),
            Text(""),
            Text("Workspaces", style="bold"),
            Text(""),
        ]
        if not self.workspaces:
            parts.append(Text("  (none)", style="dim"))
        for ws in self.workspaces:
            parts.append(Text(f"  · {ws.name:<24} id={ws.id}"))
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Workspaces  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _roles_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("ENTERPRISE", style="bold bright_white"),
            Text(""),
            Text("Roles", style="bold"),
            Text(""),
        ]
        for role, perms in role_matrix().items():
            parts.append(Text(f"  {role}", style="bold"))
            parts.append(Text(f"    {', '.join(perms)}", style="dim"))
        parts.extend(
            [
                Text(""),
                Text("  No wildcards · least privilege by default", style="dim"),
                Text(""),
                Text("View", style="dim"),
                Text("  Roles  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _keys_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("ENTERPRISE", style="bold bright_white"),
            Text(""),
            Text("API Keys", style="bold"),
            Text(""),
        ]
        if not self.api_keys:
            parts.append(Text("  (none)", style="dim"))
        for key in self.api_keys:
            status = "revoked" if key.revoked else "active"
            parts.append(
                Text(
                    f"  · {key.prefix}…  {status}  "
                    f"scopes={len(key.scopes)}  ws={key.workspace_id}"
                )
            )
        parts.extend(
            [
                Text(""),
                Text(
                    "  Raw secrets never re-exposed after create/rotate.", style="dim"
                ),
                Text(""),
                Text("View", style="dim"),
                Text("  API Keys  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _audit_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("ENTERPRISE", style="bold bright_white"),
            Text(""),
            Text("Audit", style="bold"),
            Text(f"  Total: {self.audit_count:,}"),
            Text(""),
        ]
        recent = self.audit_events[-8:]
        if not recent:
            parts.append(Text("  (none)", style="dim"))
        for event in recent:
            parts.append(
                Text(f"  · {event.action:<22} {event.actor} → {event.resource}")
            )
        parts.extend(
            [
                Text(""),
                Text("  Append-only · deletion never allowed", style="dim"),
                Text(""),
                Text("View", style="dim"),
                Text("  Audit  (] cycles)"),
            ]
        )
        return Group(*parts)

    def _compliance_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("ENTERPRISE", style="bold bright_white"),
            Text(""),
            Text("Compliance", style="bold"),
            Text(""),
            Text(f"  Status: {self.compliance_status}"),
            Text(""),
            Text("  Reports", style="bold"),
            Text("  · SOC2 Readiness"),
            Text("  · ISO 27001 Mapping"),
            Text("  · Audit Summary"),
            Text("  · Access Report"),
            Text(""),
            Text("  Formats: Markdown + JSON", style="dim"),
            Text(""),
            Text("View", style="dim"),
            Text("  Compliance  (] cycles)"),
        ]
        return Group(*parts)

    def _analytics_view(self) -> RenderableType:
        parts: list[Text] = [
            Text("ENTERPRISE", style="bold bright_white"),
            Text(""),
            Text("Analytics", style="bold"),
            Text(""),
        ]
        if self.metrics is None:
            parts.append(Text("  (no metrics)", style="dim"))
        else:
            m = self.metrics
            parts.extend(
                [
                    Text(f"  API usage            {m.api_usage:,}"),
                    Text(f"  Plugin usage         {m.plugin_usage:,}"),
                    Text(f"  Research activity    {m.research_activity:,}"),
                    Text(f"  Simulations          {m.simulation_counts:,}"),
                    Text(f"  Policy evaluations   {m.policy_evaluations:,}"),
                ]
            )
        parts.extend(
            [
                Text(""),
                Text("View", style="dim"),
                Text("  Analytics  (] cycles)"),
            ]
        )
        return Group(*parts)
