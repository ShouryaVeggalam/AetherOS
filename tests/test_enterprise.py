"""Tests for v5.0 P5 Enterprise Edition."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from rich.console import Console

from aetheros.enterprise import (
    ADMIN,
    ALL_PERMISSIONS,
    ANALYST,
    ENGINEER,
    MANAGE_PLUGINS,
    MANAGE_POLICIES,
    READ_CONTEXT,
    READ_GRAPH,
    VIEWER,
    AnalyticsService,
    APIKey,
    APIKeyService,
    AuditEvent,
    AuditLog,
    ComplianceService,
    EnterprisePanel,
    Member,
    Organization,
    OrganizationService,
    Workspace,
    WorkspaceService,
    has_permission,
    permissions_for,
    require_permission,
    role_matrix,
    seed_demo_enterprise,
    validate_scopes,
)


def _print(renderable: object) -> str:
    console = Console(record=True, width=100)
    console.print(renderable)
    return console.export_text()


def test_rbac_least_privilege() -> None:
    assert VIEWER in role_matrix()
    assert permissions_for(VIEWER) == frozenset({READ_GRAPH, READ_CONTEXT})
    assert MANAGE_POLICIES in permissions_for(ADMIN)
    assert MANAGE_PLUGINS in permissions_for(ENGINEER)
    assert MANAGE_PLUGINS not in permissions_for(ANALYST)
    assert has_permission(ADMIN, MANAGE_POLICIES)
    assert not has_permission(VIEWER, MANAGE_POLICIES)
    require_permission(ADMIN, READ_GRAPH)
    with pytest.raises(PermissionError):
        require_permission(VIEWER, MANAGE_POLICIES)
    with pytest.raises(ValueError):
        permissions_for("NOPE")
    with pytest.raises(ValueError):
        has_permission(VIEWER, "WRITE_ALL")
    scopes = validate_scopes([READ_GRAPH, "read_context"])
    assert READ_CONTEXT in scopes
    with pytest.raises(ValueError, match="wildcard"):
        validate_scopes(["*"])
    with pytest.raises(ValueError):
        validate_scopes([])
    with pytest.raises(ValueError):
        validate_scopes(["  "])
    assert MANAGE_POLICIES in ALL_PERMISSIONS


def test_organizations_and_workspaces(tmp_path: Path) -> None:
    audit = AuditLog(root=tmp_path)
    orgs = OrganizationService(root=tmp_path, audit=audit)
    org = orgs.create("CELESTRA", actor="admin")
    assert orgs.get(org.id) is not None
    assert orgs.list()[0].name == "CELESTRA"
    spaces = WorkspaceService(root=tmp_path, audit=audit)
    ws = spaces.create(org.id, "Platform", actor="admin")
    assert spaces.get(ws.id) is not None
    mem = spaces.add_member(ws.id, "ada@celestra", ADMIN, performed_by="admin")
    assert mem.role == ADMIN
    assert spaces.list_members(ws.id)
    assert spaces.member_count(organization_id=org.id) == 1
    assert spaces.list(organization_id=org.id)
    with pytest.raises(KeyError):
        spaces.add_member("missing", "x", VIEWER)
    with pytest.raises(ValueError):
        spaces.create("", "x")
    # persistence
    orgs2 = OrganizationService(root=tmp_path)
    assert orgs2.get(org.id) is not None
    assert any(e.action == "Organization Created" for e in audit.list())
    assert any(e.action == "Workspace Created" for e in audit.list())


def test_models_validation() -> None:
    with pytest.raises(ValueError):
        Organization(id="", name="x", created_at=datetime.now(UTC))
    with pytest.raises(ValueError):
        Workspace(id="w", organization_id="", name="n")
    with pytest.raises(ValueError):
        Member(id="m", workspace_id="w", actor="a", role="GOD")
    key = APIKey(
        id="k",
        workspace_id="w",
        scopes=(READ_GRAPH,),
        created_at=datetime.now(UTC),
        expires_at=None,
        key_hash="abc",
        prefix="aether_",
    )
    assert key.workspace == "w"
    assert APIKey.from_dict(key.to_dict()).id == "k"
    event = AuditEvent(
        actor="a",
        action="X",
        resource="r",
        timestamp=datetime.now(UTC),
        metadata=(("k", "v"),),
    )
    assert AuditEvent.from_dict(event.to_dict()).action == "X"


def test_api_keys_lifecycle(tmp_path: Path) -> None:
    audit = AuditLog(root=tmp_path)
    keys = APIKeyService(root=tmp_path, audit=audit)
    issued = keys.create("ws-1", (READ_GRAPH, READ_CONTEXT), actor="admin")
    assert issued.secret.startswith("aether_")
    assert keys.validate(issued.secret) is not None
    assert keys.get(issued.key.id) is not None
    # raw secret not stored in JSON
    raw_store = (tmp_path / "api_keys.json").read_text(encoding="utf-8")
    assert issued.secret not in raw_store
    rotated = keys.rotate(issued.key.id, actor="admin")
    assert keys.validate(issued.secret) is None
    assert keys.validate(rotated.secret) is not None
    keys.revoke(rotated.key.id, actor="admin")
    assert keys.validate(rotated.secret) is None
    assert keys.revoke(rotated.key.id).revoked is True
    with pytest.raises(KeyError):
        keys.revoke("missing")
    with pytest.raises(KeyError):
        keys.rotate("missing")
    # expired key
    issued2 = keys.create("ws-1", (READ_GRAPH,), actor="admin", ttl_days=None)
    # craft expired by rewriting metadata
    expired = APIKey(
        id=issued2.key.id,
        workspace_id=issued2.key.workspace_id,
        scopes=issued2.key.scopes,
        created_at=issued2.key.created_at,
        expires_at=datetime.now(UTC) - timedelta(days=1),
        key_hash=issued2.key.key_hash,
        prefix=issued2.key.prefix,
        revoked=False,
        label=issued2.key.label,
    )
    keys._keys[expired.id] = expired
    keys._write()
    assert keys.validate(issued2.secret) is None
    assert keys.list(workspace_id="ws-1")
    assert any(e.action == "API Key Rotated" for e in audit.list())


def test_audit_append_only(tmp_path: Path) -> None:
    log = AuditLog(root=tmp_path)
    e1 = log.append(actor="a", action="Policy Created", resource="p1")
    e2 = log.append(actor="b", action="Plugin Installed", resource="plug")
    assert log.count() == 2
    assert log.list(action="Policy Created")[0].id == e1.id
    assert log.list(actor="b")[0].id == e2.id
    assert len(log.list(limit=1)) == 1
    # corrupt line skipped
    with log.path.open("a", encoding="utf-8") as handle:
        handle.write("{bad\n")
    log._loaded = False
    assert log.count() >= 2
    # no delete API
    assert not hasattr(log, "delete")
    assert not hasattr(log, "clear")


def test_compliance_reports(tmp_path: Path) -> None:
    bundle = seed_demo_enterprise(tmp_path / "ent")
    svc = ComplianceService(
        audit=bundle.audit,
        organizations=bundle.organizations.list(),
        workspaces=bundle.workspaces.list(),
        members=bundle.all_members(),
        api_keys=bundle.api_keys.list(),
    )
    soc2 = svc.soc2_readiness()
    assert "SOC2" in soc2.markdown
    assert '"ready"' in soc2.to_json()
    iso = svc.iso27001_mapping()
    assert "ISO 27001" in iso.markdown
    summary = svc.audit_summary()
    assert summary.data["total"] >= 1
    access = svc.access_report()
    assert "Access Report" in access.markdown
    assert "role_matrix" in access.data


def test_analytics(tmp_path: Path) -> None:
    analytics = AnalyticsService(root=tmp_path)
    analytics.record_api_usage(3)
    analytics.record_plugin_usage(2)
    analytics.record_research_activity()
    analytics.record_simulation(4)
    analytics.record_policy_evaluation(5)
    snap = analytics.snapshot()
    assert snap.api_usage == 3
    assert snap.plugin_usage == 2
    assert snap.research_activity == 1
    assert snap.simulation_counts == 4
    assert snap.policy_evaluations == 5
    with pytest.raises(ValueError):
        analytics.record_api_usage(-1)
    # reload
    a2 = AnalyticsService(root=tmp_path)
    assert a2.snapshot().api_usage == 3


def test_formatter_views(tmp_path: Path) -> None:
    bundle = seed_demo_enterprise(tmp_path / "ent")
    idle = _print(EnterprisePanel())
    assert "idle" in idle.lower()
    panel = EnterprisePanel(
        organization=bundle.organization,
        workspaces=bundle.workspaces.list(),
        members=bundle.all_members(),
        api_keys=bundle.api_keys.list(),
        audit_events=bundle.audit.list(limit=10),
        audit_count=bundle.audit.count(),
        compliance_status=bundle.compliance_status(),
        metrics=bundle.analytics.snapshot(),
        view="organizations",
    )
    text = _print(panel)
    assert "CELESTRA" in text
    assert "SOC2 Ready" in text
    for view in (
        "workspaces",
        "roles",
        "api_keys",
        "audit",
        "compliance",
        "analytics",
    ):
        assert "ENTERPRISE" in _print(
            EnterprisePanel(
                organization=bundle.organization,
                workspaces=bundle.workspaces.list(),
                members=bundle.all_members(),
                api_keys=bundle.api_keys.list(),
                audit_events=bundle.audit.list(limit=5),
                audit_count=bundle.audit.count(),
                metrics=bundle.analytics.snapshot(),
                view=view,
            )
        )
    empty = _print(
        EnterprisePanel(
            organization=bundle.organization,
            workspaces=(),
            view="workspaces",
        )
    )
    assert "none" in empty.lower()
    empty_keys = _print(
        EnterprisePanel(organization=bundle.organization, api_keys=(), view="api_keys")
    )
    assert "none" in empty_keys.lower()
    empty_audit = _print(
        EnterprisePanel(
            organization=bundle.organization,
            audit_events=(),
            audit_count=0,
            view="audit",
        )
    )
    assert "none" in empty_audit.lower()
    empty_metrics = _print(
        EnterprisePanel(
            organization=bundle.organization, metrics=None, view="analytics"
        )
    )
    assert "no metrics" in empty_metrics.lower()


def test_seed_idempotent(tmp_path: Path) -> None:
    a = seed_demo_enterprise(tmp_path / "ent")
    b = seed_demo_enterprise(tmp_path / "ent")
    assert a.organization is not None
    assert b.organization is not None
    assert a.organization.id == b.organization.id
    assert len(a.workspaces.list()) == 4


def test_org_corrupt_store(tmp_path: Path) -> None:
    orgs = OrganizationService(root=tmp_path)
    orgs.store_path.parent.mkdir(parents=True, exist_ok=True)
    orgs.store_path.write_text("[]\n", encoding="utf-8")
    orgs._loaded = False
    assert orgs.list() == ()
    spaces = WorkspaceService(root=tmp_path)
    spaces.store_path.write_text("[]\n", encoding="utf-8")
    spaces._loaded = False
    assert spaces.list() == ()


def test_model_from_dict_and_edges() -> None:
    with pytest.raises(ValueError):
        Organization(id="o", name="", created_at=datetime.now(UTC))
    with pytest.raises(ValueError):
        Workspace(id="", organization_id="o", name="n")
    with pytest.raises(ValueError):
        Workspace(id="w", organization_id="o", name="")
    with pytest.raises(ValueError):
        Member(id="", workspace_id="w", actor="a", role=VIEWER)
    org = Organization.from_dict(
        {"id": "o1", "name": "N", "created_at": datetime.now(UTC).isoformat()}
    )
    assert org.id == "o1"
    ws = Workspace.from_dict({"id": "w1", "organization_id": "o1", "name": "Platform"})
    assert ws.name == "Platform"
    mem = Member.from_dict(
        {"id": "m1", "workspace_id": "w1", "actor": "a", "role": "viewer"}
    )
    assert mem.role == VIEWER
    with pytest.raises(ValueError):
        APIKey(
            id="",
            workspace_id="w",
            scopes=(READ_GRAPH,),
            created_at=datetime.now(UTC),
            expires_at=None,
            key_hash="h",
            prefix="p",
        )
    with pytest.raises(ValueError):
        APIKey(
            id="k",
            workspace_id="",
            scopes=(READ_GRAPH,),
            created_at=datetime.now(UTC),
            expires_at=None,
            key_hash="h",
            prefix="p",
        )
    with pytest.raises(ValueError):
        APIKey(
            id="k",
            workspace_id="w",
            scopes=(),
            created_at=datetime.now(UTC),
            expires_at=None,
            key_hash="h",
            prefix="p",
        )
    with pytest.raises(ValueError):
        APIKey(
            id="k",
            workspace_id="w",
            scopes=(READ_GRAPH,),
            created_at=datetime.now(UTC),
            expires_at=None,
            key_hash="",
            prefix="p",
        )
    key = APIKey.from_dict(
        {
            "id": "k1",
            "workspace": "w1",
            "scopes": "READ_GRAPH",
            "created_at": datetime.now(UTC).isoformat(),
            "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "key_hash": "deadbeef",
            "prefix": "aether_xxxx",
        }
    )
    assert key.scopes == (READ_GRAPH,)
    with pytest.raises(ValueError):
        AuditEvent(actor="", action="a", resource="r", timestamp=datetime.now(UTC))
    with pytest.raises(ValueError):
        AuditEvent(actor="a", action="", resource="r", timestamp=datetime.now(UTC))
    with pytest.raises(ValueError):
        AuditEvent(actor="a", action="a", resource="", timestamp=datetime.now(UTC))
    # metadata non-dict
    ev = AuditEvent.from_dict(
        {
            "actor": "a",
            "action": "X",
            "resource": "r",
            "timestamp": datetime.now(UTC).isoformat(),
            "metadata": "nope",
        }
    )
    assert ev.metadata == ()


def test_api_keys_validate_miss_and_corrupt(tmp_path: Path) -> None:
    keys = APIKeyService(root=tmp_path)
    assert keys.validate("aether_not_real") is None
    keys.store_path.parent.mkdir(parents=True, exist_ok=True)
    keys.store_path.write_text("[]\n", encoding="utf-8")
    keys._loaded = False
    assert keys.list() == ()
    keys.store_path.write_text(
        json.dumps(
            {
                "api_keys": [
                    "bad",
                    {
                        "id": "k9",
                        "workspace_id": "w",
                        "scopes": [READ_GRAPH],
                        "created_at": datetime.now(UTC).isoformat(),
                        "expires_at": None,
                        "key_hash": "abc",
                        "prefix": "aether_abc",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    keys._loaded = False
    assert keys.get("k9") is not None


def test_workspaces_member_count_and_corrupt(tmp_path: Path) -> None:
    audit = AuditLog(root=tmp_path)
    orgs = OrganizationService(root=tmp_path, audit=audit)
    spaces = WorkspaceService(root=tmp_path, audit=audit)
    org = orgs.create("X", actor="a")
    ws = spaces.create(org.id, "W", actor="a")
    spaces.add_member(ws.id, "u", VIEWER, performed_by="a")
    assert spaces.member_count() == 1
    spaces.store_path.write_text(
        json.dumps(
            {
                "workspaces": [
                    "bad",
                    {"id": "w2", "organization_id": "o", "name": "N"},
                ],
                "members": [
                    "bad",
                    {"id": "m2", "workspace_id": "w2", "actor": "u", "role": "VIEWER"},
                ],
            }
        ),
        encoding="utf-8",
    )
    spaces._loaded = False
    assert spaces.get("w2") is not None
    assert spaces.list_members("w2")


def test_demo_helpers_and_rbac_unknown_scope(tmp_path: Path) -> None:
    from aetheros.enterprise.demo import bundle_audit, bundle_keys, bundle_metrics

    bundle = seed_demo_enterprise(tmp_path / "ent")
    assert bundle_metrics(bundle).api_usage >= 0
    assert bundle_keys(bundle)
    assert bundle_audit(bundle, limit=3)
    with pytest.raises(ValueError):
        validate_scopes(["NOT_A_REAL_SCOPE"])
    analytics = AnalyticsService(root=tmp_path / "bad")
    analytics.store_path.parent.mkdir(parents=True, exist_ok=True)
    analytics.store_path.write_text("[]\n", encoding="utf-8")
    analytics._loaded = False
    assert analytics.snapshot().api_usage == 0
