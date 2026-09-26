"""Tests for AetherOS v6.0 P1 Cloud Federation Engine (read-only)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from rich.console import Console

from aetheros.cloud import (
    PROVIDER_IDS,
    RESOURCE_TYPES,
    AWSProvider,
    AzureProvider,
    CloudFederationEngine,
    CloudFederationPanel,
    CloudProvider,
    CloudRegistry,
    CloudResource,
    DockerProvider,
    EdgeProvider,
    FederationHealth,
    GCPProvider,
    InfrastructureSnapshot,
    KubernetesProvider,
    SnapshotDiff,
    capture,
    compare,
    decode_snapshot,
    deserialize,
    encode_snapshot,
    hash_snapshot,
    seed_demo_cloud,
    serialize,
    topology_hash,
)


def test_provider_ids_and_resource_types() -> None:
    assert "aws" in PROVIDER_IDS
    assert "kubernetes" in PROVIDER_IDS
    assert "ec2" in RESOURCE_TYPES
    assert "pod" in RESOURCE_TYPES
    assert "gateway" in RESOURCE_TYPES


def test_cloud_provider_validation_and_roundtrip() -> None:
    provider = CloudProvider(
        id="aws-1",
        name="AWS",
        version="2016-11-15",
        region="us-east-1",
        connected=True,
    )
    assert CloudProvider.from_dict(provider.to_dict()) == provider
    with pytest.raises(ValueError):
        CloudProvider(id="", name="AWS", version="1", region="r")


def test_cloud_resource_normalization_and_roundtrip() -> None:
    resource = CloudResource(
        id="i-1",
        provider="aws",
        type="ec2",
        name="web",
        region="us-east-1",
        metadata={"state": "running"},
    )
    assert CloudResource.from_dict(resource.to_dict()).name == "web"
    with pytest.raises(ValueError):
        CloudResource.from_dict(
            {
                "id": "x",
                "provider": "aws",
                "type": "ec2",
                "name": "n",
                "region": "r",
                "metadata": "bad",
            }
        )


def test_infrastructure_snapshot_regions_and_roundtrip() -> None:
    provider = CloudProvider(id="aws-1", name="AWS", version="1", region="us-east-1")
    resource = CloudResource(
        id="i-1",
        provider="aws",
        type="ec2",
        name="web",
        region="eu-west-1",
        metadata={},
    )
    snap = capture(
        (provider,), (resource,), timestamp=datetime(2026, 9, 26, tzinfo=UTC)
    )
    assert snap.provider_count == 1
    assert snap.resource_count == 1
    assert snap.regions == ("us-east-1", "eu-west-1")
    assert snap.topology_hash.startswith("sha256:")
    restored = InfrastructureSnapshot.from_dict(snap.to_dict())
    assert restored.topology_hash == snap.topology_hash


def test_federation_health_label() -> None:
    healthy = FederationHealth(online=3, degraded=0, offline=0, confidence=1.0)
    assert healthy.label == "online"
    assert healthy.total == 3
    degraded = FederationHealth(online=1, degraded=1, offline=0, confidence=0.75)
    assert degraded.label == "degraded"
    offline = FederationHealth(online=0, degraded=0, offline=2, confidence=0.0)
    assert offline.label == "offline"
    assert FederationHealth.from_dict(healthy.to_dict()).online == 3
    with pytest.raises(ValueError):
        FederationHealth(online=0, degraded=0, offline=0, confidence=1.5)


def test_aws_provider_filters_unsupported_types() -> None:
    aws = AWSProvider()
    resources = aws.observe(
        [
            {"id": "i-1", "type": "ec2", "name": "a", "region": "us-east-1"},
            {"id": "bad", "type": "lambda", "name": "fn", "region": "us-east-1"},
        ]
    )
    assert len(resources) == 1
    assert resources[0].type == "ec2"
    assert resources[0].provider == "aws"


def test_all_providers_demo_inventory() -> None:
    adapters = [
        AWSProvider(),
        AzureProvider(),
        GCPProvider(),
        KubernetesProvider(),
        DockerProvider(),
        EdgeProvider(),
    ]
    for adapter in adapters:
        resources = adapter.observe()
        assert resources
        assert all(r.provider == adapter.kind for r in resources)


def test_registry_tracks_providers_regions_health() -> None:
    registry = CloudRegistry(healthy_age_sec=10, degraded_age_sec=30)
    now = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)
    provider = CloudProvider(
        id="aws-1", name="AWS", version="1", region="us-east-1", connected=True
    )
    resources = (
        CloudResource(
            id="i-1",
            provider="aws",
            type="ec2",
            name="web",
            region="us-west-2",
            metadata={},
        ),
    )
    registry.register(provider, resources=resources, now=now)
    assert registry.get("aws-1") is not None
    assert "us-east-1" in registry.list_regions()
    assert "us-west-2" in registry.list_regions()
    assert len(registry.all_resources()) == 1

    health = registry.health(now=now)
    assert health.online == 1
    assert health.confidence == 1.0

    degraded_now = now + timedelta(seconds=15)
    health = registry.health(now=degraded_now)
    assert health.degraded == 1

    offline_now = now + timedelta(seconds=60)
    health = registry.health(now=offline_now)
    assert health.offline == 1
    assert registry.max_snapshot_age(now=offline_now) >= 60


def test_registry_offline_when_disconnected() -> None:
    registry = CloudRegistry()
    provider = CloudProvider(
        id="aws-1",
        name="AWS",
        version="1",
        region="us-east-1",
        connected=False,
    )
    registry.register(provider)
    health = registry.health()
    assert health.offline == 1


def test_registry_rejects_bad_thresholds() -> None:
    with pytest.raises(ValueError):
        CloudRegistry(healthy_age_sec=100, degraded_age_sec=10)


def test_snapshot_serialize_compare_hash() -> None:
    p1 = CloudProvider(id="a", name="A", version="1", region="r1")
    p2 = CloudProvider(id="b", name="B", version="1", region="r2")
    r1 = CloudResource(
        id="res-1", provider="aws", type="ec2", name="n1", region="r1", metadata={}
    )
    r2 = CloudResource(
        id="res-2", provider="aws", type="ebs", name="n2", region="r1", metadata={}
    )
    left = capture((p1,), (r1,))
    right = capture((p1, p2), (r1, r2))
    text = serialize(left, pretty=True)
    assert '"topology_hash"' in text
    restored = deserialize(text)
    assert restored.topology_hash == left.topology_hash
    assert encode_snapshot(left) == serialize(left, pretty=False)
    assert decode_snapshot(encode_snapshot(left)).resource_count == 1

    diff = compare(left, right)
    assert isinstance(diff, SnapshotDiff)
    assert not diff.identical
    assert "b" in diff.added_providers
    assert "res-2" in diff.added_resources
    assert diff.hash_changed
    assert hash_snapshot(left) == left.topology_hash
    assert topology_hash(left.providers, left.resources) == left.topology_hash
    assert diff.to_dict()["identical"] is False


def test_federation_engine_capture_and_view() -> None:
    engine = CloudFederationEngine()
    snap = engine.capture_all()
    assert snap.provider_count == 6
    assert snap.resource_count >= 10
    assert engine.verify_hash()
    view = engine.view()
    assert view.health.online >= 1
    assert len(view.records) == 6
    assert "AWS" in engine.serialize_last()

    other = capture(snap.providers[:1], snap.resources[:1])
    diff = engine.compare_with(other)
    assert diff.hash_changed or diff.removed_providers or diff.removed_resources


def test_federation_engine_empty_inventory_mode() -> None:
    engine = CloudFederationEngine()
    snap = engine.capture_all(use_demo=False, inventories={})
    # Providers still registered; resources empty when inventories are empty lists.
    assert snap.provider_count == 6
    assert snap.resource_count == 0


def test_seed_demo_cloud() -> None:
    engine = seed_demo_cloud()
    assert engine.last_snapshot is not None
    assert engine.last_snapshot.provider_count == 6


def test_formatter_views_render() -> None:
    engine = seed_demo_cloud()
    view = engine.view()
    console = Console(record=True, width=100)
    for name in ("providers", "regions", "resources", "health", "snapshots"):
        panel = CloudFederationPanel(
            snapshot=view.snapshot,
            health=view.health,
            records=view.records,
            snapshot_age_seconds=view.snapshot_age_seconds,
            view=name,
        )
        console.print(panel)
        text = console.export_text()
        assert "CLOUD FEDERATION" in text or "Cloud Federation" in text
        assert "Read Only" in text
    idle = CloudFederationPanel()
    console.print(idle)
    assert (
        "idle" in console.export_text().lower() or "Read Only" in console.export_text()
    )


def test_compare_requires_prior_capture() -> None:
    engine = CloudFederationEngine()
    empty = capture((), ())
    with pytest.raises(RuntimeError):
        engine.compare_with(empty)
    assert engine.verify_hash() is False
    assert engine.serialize_last() == "{}"


def test_snapshot_from_dict_validation() -> None:
    with pytest.raises(ValueError):
        InfrastructureSnapshot.from_dict(
            {
                "timestamp": "2026-09-26T00:00:00+00:00",
                "providers": "bad",
                "resources": [],
                "topology_hash": "sha256:x",
            }
        )
    with pytest.raises(ValueError):
        InfrastructureSnapshot.from_dict(
            {
                "timestamp": "2026-09-26T00:00:00+00:00",
                "providers": [],
                "resources": "bad",
                "topology_hash": "sha256:x",
            }
        )
    with pytest.raises(ValueError):
        InfrastructureSnapshot(
            timestamp=datetime.now(UTC),
            providers=(),
            resources=(),
            topology_hash="",
        )


def test_model_field_validation_edges() -> None:
    with pytest.raises(ValueError):
        CloudProvider(id="x", name="", version="1", region="r")
    with pytest.raises(ValueError):
        CloudProvider(id="x", name="n", version="", region="r")
    with pytest.raises(ValueError):
        CloudProvider(id="x", name="n", version="1", region="")
    with pytest.raises(ValueError):
        CloudResource(id="", provider="aws", type="ec2", name="n", region="r")
    with pytest.raises(ValueError):
        CloudResource(id="i", provider="", type="ec2", name="n", region="r")
    with pytest.raises(ValueError):
        CloudResource(id="i", provider="aws", type="", name="n", region="r")
    with pytest.raises(ValueError):
        CloudResource(id="i", provider="aws", type="ec2", name="", region="r")
    with pytest.raises(ValueError):
        CloudResource(id="i", provider="aws", type="ec2", name="n", region="")
    with pytest.raises(ValueError):
        FederationHealth(online=-1, degraded=0, offline=0, confidence=0.5)
    from aetheros.cloud.models import ProviderRecord

    provider = CloudProvider(id="x", name="n", version="1", region="r")
    with pytest.raises(ValueError):
        ProviderRecord(
            provider=provider,
            status="nope",  # type: ignore[arg-type]
            api_version="1",
            snapshot_age_seconds=0,
            last_seen=datetime.now(UTC),
        )
    with pytest.raises(ValueError):
        ProviderRecord(
            provider=provider,
            status="healthy",
            api_version="",
            snapshot_age_seconds=0,
            last_seen=datetime.now(UTC),
        )
    with pytest.raises(ValueError):
        ProviderRecord(
            provider=provider,
            status="healthy",
            api_version="1",
            snapshot_age_seconds=-1,
            last_seen=datetime.now(UTC),
        )
    with pytest.raises(ValueError):
        ProviderRecord(
            provider=provider,
            status="healthy",
            api_version="1",
            snapshot_age_seconds=0,
            last_seen=datetime.now(UTC),
            resource_count=-1,
        )


def test_registry_status_override_and_naive_timestamps() -> None:
    registry = CloudRegistry(healthy_age_sec=10, degraded_age_sec=30)
    naive = datetime(2026, 9, 26, 12, 0, 0)
    provider = CloudProvider(
        id="aws-1", name="AWS", version="1", region="us-east-1", connected=True
    )
    record = registry.register(provider, now=naive, status="unknown")
    assert record.status == "unknown"
    assert registry.resources_for("missing") == ()
    with pytest.raises(ValueError):
        CloudRegistry(healthy_age_sec=0, degraded_age_sec=10)
    # empty health
    empty = CloudRegistry()
    assert empty.health().confidence == 0.0
    assert empty.max_snapshot_age() == 0.0
    # refresh with naive clock + naive last_seen on stored record
    from aetheros.cloud.models import ProviderRecord

    registry._records["aws-1"] = ProviderRecord(
        provider=provider,
        status="healthy",
        api_version="1",
        snapshot_age_seconds=0.0,
        last_seen=naive,
        resource_count=0,
    )
    registry.refresh_ages(now=naive + timedelta(seconds=1))
    assert registry.get("aws-1") is not None


def test_serializer_edges() -> None:
    from aetheros.cloud.serializer import snapshot_to_json

    snap = capture((), ())
    compact = snapshot_to_json(snap, indent=None)
    assert compact.startswith("{")
    with pytest.raises(ValueError):
        decode_snapshot("[]")
    with pytest.raises(ValueError):
        decode_snapshot('"x"')


def test_snapshot_naive_timestamp() -> None:
    snap = capture((), (), timestamp=datetime(2026, 1, 1, 0, 0, 0))
    assert snap.timestamp.tzinfo is not None


def test_view_captures_when_empty() -> None:
    engine = CloudFederationEngine()
    view = engine.view()
    assert view.snapshot.provider_count == 6


def test_formatter_status_variants() -> None:
    from aetheros.cloud.models import ProviderRecord

    now = datetime.now(UTC)
    records = (
        ProviderRecord(
            provider=CloudProvider(
                id="k8s", name="Kubernetes", version="1", region="r", connected=True
            ),
            status="degraded",
            api_version="1",
            snapshot_age_seconds=12,
            last_seen=now,
        ),
        ProviderRecord(
            provider=CloudProvider(
                id="aws", name="AWS", version="1", region="r", connected=True
            ),
            status="offline",
            api_version="1",
            snapshot_age_seconds=99,
            last_seen=now,
        ),
        ProviderRecord(
            provider=CloudProvider(
                id="az", name="Azure", version="1", region="r", connected=True
            ),
            status="unknown",
            api_version="1",
            snapshot_age_seconds=1,
            last_seen=now,
        ),
    )
    snap = capture(tuple(r.provider for r in records), ())
    health = FederationHealth(online=0, degraded=1, offline=1, confidence=0.25)
    panel = CloudFederationPanel(
        snapshot=snap,
        health=health,
        records=records,
        snapshot_age_seconds=12,
        view="health",
    )
    console = Console(record=True, width=100)
    console.print(panel)
    text = console.export_text()
    assert "Degraded" in text
    assert "Offline" in text
    assert "Unknown" in text


def test_non_aws_providers_skip_unsupported() -> None:
    assert AzureProvider().observe([{"id": "x", "type": "sql", "name": "n"}]) == ()
    assert GCPProvider().observe([{"id": "x", "type": "bucket", "name": "n"}]) == ()
    assert (
        KubernetesProvider().observe([{"id": "x", "type": "ingress", "name": "n"}])
        == ()
    )
    assert DockerProvider().observe([{"id": "x", "type": "volume", "name": "n"}]) == ()
    assert EdgeProvider().observe([{"id": "x", "type": "satellite", "name": "n"}]) == ()
