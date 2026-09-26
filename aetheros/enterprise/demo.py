"""Demo enterprise tenancy for the dashboard panel.

Creates CELESTRA org metadata, sample workspaces, keys, audit, and metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aetheros.enterprise.analytics import AnalyticsService, UsageMetrics
from aetheros.enterprise.api_keys import APIKeyService
from aetheros.enterprise.audit import AuditLog
from aetheros.enterprise.compliance import ComplianceService
from aetheros.enterprise.models import (
    ADMIN,
    ANALYST,
    ENGINEER,
    VIEWER,
    APIKey,
    AuditEvent,
    Member,
    Organization,
    Workspace,
)
from aetheros.enterprise.organizations import OrganizationService
from aetheros.enterprise.rbac import (
    MANAGE_PLUGINS,
    MANAGE_POLICIES,
    READ_CONTEXT,
    READ_GRAPH,
    READ_REASONING,
    READ_RESEARCH,
    READ_SIMULATION,
)
from aetheros.enterprise.workspaces import WorkspaceService


@dataclass
class EnterpriseBundle:
    """In-memory handle to seeded enterprise services for the UI."""

    root: Path
    audit: AuditLog
    organizations: OrganizationService
    workspaces: WorkspaceService
    api_keys: APIKeyService
    analytics: AnalyticsService
    organization: Organization | None = None

    def all_members(self) -> tuple[Member, ...]:
        """Flatten members across workspaces."""

        members: list[Member] = []
        for ws in self.workspaces.list():
            members.extend(self.workspaces.list_members(ws.id))
        return tuple(members)

    def compliance_status(self) -> str:
        """Return a short compliance label for the summary panel."""

        report = ComplianceService(
            audit=self.audit,
            organizations=self.organizations.list(),
            workspaces=self.workspaces.list(),
            members=self.all_members(),
            api_keys=self.api_keys.list(),
        ).soc2_readiness()
        return "SOC2 Ready" if report.data.get("ready") else "Gaps Remain"


def seed_demo_enterprise(root: Path | None = None) -> EnterpriseBundle:
    """Idempotent demo seed for CELESTRA enterprise tenancy."""

    base = Path(root) if root else Path("data/enterprise_demo")
    audit = AuditLog(root=base)
    orgs = OrganizationService(root=base, audit=audit)
    spaces = WorkspaceService(root=base, audit=audit)
    keys = APIKeyService(root=base, audit=audit)
    analytics = AnalyticsService(root=base)

    existing = orgs.list()
    if existing:
        org = next((o for o in existing if o.name == "CELESTRA"), existing[0])
    else:
        org = orgs.create("CELESTRA", actor="bootstrap")
        names = ("Platform", "Research", "Simulation", "Edge")
        created_ws: list[Workspace] = []
        for name in names:
            created_ws.append(spaces.create(org.id, name, actor="bootstrap"))
        roster = (
            ("ada@celestra", ADMIN),
            ("bob@celestra", ENGINEER),
            ("cara@celestra", ANALYST),
            ("drew@celestra", VIEWER),
        )
        for ws in created_ws:
            for actor, role in roster:
                spaces.add_member(ws.id, actor, role, performed_by="bootstrap")
        for i in range(14):
            spaces.add_member(
                created_ws[i % len(created_ws)].id,
                f"user{i:02d}@celestra",
                VIEWER,
                performed_by="bootstrap",
            )
        for ws in created_ws[:3]:
            keys.create(
                ws.id,
                (READ_GRAPH, READ_CONTEXT, READ_REASONING),
                actor="bootstrap",
                label=f"{ws.name}-read",
            )
        keys.create(
            created_ws[0].id,
            (
                READ_GRAPH,
                READ_CONTEXT,
                READ_REASONING,
                READ_RESEARCH,
                READ_SIMULATION,
                MANAGE_PLUGINS,
                MANAGE_POLICIES,
            ),
            actor="bootstrap",
            label="admin-console",
        )
        for i in range(8):
            keys.create(
                created_ws[i % len(created_ws)].id,
                (READ_GRAPH,),
                actor="bootstrap",
                label=f"reader-{i}",
            )
        analytics.record_api_usage(1280)
        analytics.record_plugin_usage(42)
        analytics.record_research_activity(17)
        analytics.record_simulation(64)
        analytics.record_policy_evaluation(220)
        for i in range(20):
            audit.append(
                actor="system",
                action="Policy Evaluated",
                resource=f"policy-sim-{i}",
                metadata={"batch": "seed"},
            )

    return EnterpriseBundle(
        root=base,
        audit=audit,
        organizations=orgs,
        workspaces=spaces,
        api_keys=keys,
        analytics=analytics,
        organization=org,
    )


def bundle_metrics(bundle: EnterpriseBundle) -> UsageMetrics:
    """Snapshot analytics for the panel."""

    return bundle.analytics.snapshot()


def bundle_keys(bundle: EnterpriseBundle) -> tuple[APIKey, ...]:
    """List API key metadata."""

    return bundle.api_keys.list()


def bundle_audit(
    bundle: EnterpriseBundle, *, limit: int = 20
) -> tuple[AuditEvent, ...]:
    """Recent audit events for the panel."""

    return bundle.audit.list(limit=limit)
