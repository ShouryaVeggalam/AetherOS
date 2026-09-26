"""Enterprise Edition — v5.0 P5 governance wrappers.

Organizations · workspaces · RBAC · API keys · audit · compliance · analytics.
Does not modify Resource Graph, Reasoning, Twin, Scheduler, Consensus, or core runtime.
"""

from __future__ import annotations

from aetheros.enterprise.analytics import AnalyticsService, UsageMetrics
from aetheros.enterprise.api_keys import APIKeyService, IssuedAPIKey
from aetheros.enterprise.audit import AuditLog
from aetheros.enterprise.compliance import ComplianceReport, ComplianceService
from aetheros.enterprise.demo import (
    EnterpriseBundle,
    bundle_audit,
    bundle_keys,
    bundle_metrics,
    seed_demo_enterprise,
)
from aetheros.enterprise.formatter import EnterprisePanel
from aetheros.enterprise.models import (
    ADMIN,
    ANALYST,
    ENGINEER,
    ROLES,
    VIEWER,
    APIKey,
    AuditEvent,
    Member,
    Organization,
    Workspace,
)
from aetheros.enterprise.organizations import OrganizationService
from aetheros.enterprise.rbac import (
    ALL_PERMISSIONS,
    MANAGE_PLUGINS,
    MANAGE_POLICIES,
    READ_CONTEXT,
    READ_GRAPH,
    READ_REASONING,
    READ_RESEARCH,
    READ_SIMULATION,
    has_permission,
    permissions_for,
    require_permission,
    role_matrix,
    validate_scopes,
)
from aetheros.enterprise.workspaces import WorkspaceService

__all__ = [
    "ADMIN",
    "ALL_PERMISSIONS",
    "ANALYST",
    "APIKey",
    "APIKeyService",
    "AnalyticsService",
    "AuditEvent",
    "AuditLog",
    "ComplianceReport",
    "ComplianceService",
    "ENGINEER",
    "EnterpriseBundle",
    "EnterprisePanel",
    "IssuedAPIKey",
    "MANAGE_PLUGINS",
    "MANAGE_POLICIES",
    "Member",
    "Organization",
    "OrganizationService",
    "READ_CONTEXT",
    "READ_GRAPH",
    "READ_REASONING",
    "READ_RESEARCH",
    "READ_SIMULATION",
    "ROLES",
    "UsageMetrics",
    "VIEWER",
    "Workspace",
    "WorkspaceService",
    "bundle_audit",
    "bundle_keys",
    "bundle_metrics",
    "has_permission",
    "permissions_for",
    "require_permission",
    "role_matrix",
    "seed_demo_enterprise",
    "validate_scopes",
]
