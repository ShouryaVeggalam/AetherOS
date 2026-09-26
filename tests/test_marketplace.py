"""Tests for v5.0 P3 Extension Marketplace."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from rich.console import Console

from aetheros.marketplace import (
    ALLOWED_PERMISSIONS,
    READ_CONTEXT,
    READ_GRAPH,
    READ_TELEMETRY,
    DiscoveryQuery,
    InstalledPlugin,
    MarketplaceDiscovery,
    MarketplaceIndex,
    MarketplaceInstaller,
    MarketplacePanel,
    MarketplaceRegistry,
    MarketplaceUpdater,
    PluginManifest,
    UpdateRecommendation,
    compute_checksum,
    demo_catalog,
    is_newer,
    is_write_permission,
    normalize_permission,
    seed_demo_marketplace,
    to_sdk_capabilities,
    validate_manifest,
    validate_package,
    validate_permissions,
)


def _print(renderable: object) -> str:
    console = Console(record=True, width=100)
    console.print(renderable)
    return console.export_text()


def _manifest(**overrides: object) -> PluginManifest:
    base = dict(
        id="demo-plugin",
        name="Demo Plugin",
        version="1.0.0",
        author="Tester",
        description="unit test plugin",
        sdk_version=">=5.0.0,<6",
        category="insight",
        permissions=(READ_GRAPH, READ_CONTEXT),
        checksum="sha256:" + ("1" * 64),
    )
    base.update(overrides)
    return PluginManifest(**base)  # type: ignore[arg-type]


def test_manifest_validation_and_serde() -> None:
    m = _manifest()
    assert m.id == "demo-plugin"
    data = m.to_dict()
    assert PluginManifest.from_dict(data).name == "Demo Plugin"
    with pytest.raises(ValueError):
        PluginManifest(
            id="",
            name="x",
            version="1",
            author="a",
            description="d",
            sdk_version=">=5",
            category="c",
            permissions=(),
            checksum="sha256:abc",
        )
    with pytest.raises(ValueError):
        PluginManifest.from_dict({"id": "x", "permissions": 123})


def test_installed_and_index_serde(tmp_path: Path) -> None:
    m = _manifest()
    installed = InstalledPlugin(
        manifest=m,
        enabled=True,
        installed_at=datetime(2026, 1, 1, tzinfo=UTC),
        update_available=False,
        install_path=str(tmp_path / "demo-plugin"),
    )
    roundtrip = InstalledPlugin.from_dict(installed.to_dict())
    assert roundtrip.enabled is True
    index = MarketplaceIndex(
        plugins=(m,),
        sdk_version="5.0.0",
        generated_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    assert MarketplaceIndex.from_dict(index.to_dict()).plugins[0].id == "demo-plugin"
    with pytest.raises(ValueError):
        InstalledPlugin.from_dict({"enabled": True})
    with pytest.raises(ValueError):
        MarketplaceIndex.from_dict(
            {"plugins": "bad", "generated_at": "2026-01-01T00:00:00+00:00"}
        )


def test_permissions_reject_write() -> None:
    assert READ_GRAPH in ALLOWED_PERMISSIONS
    assert normalize_permission("graph.read") == READ_GRAPH
    assert normalize_permission("read_graph") == READ_GRAPH
    assert is_write_permission("WRITE_GRAPH")
    assert is_write_permission("graph.write")
    assert not is_write_permission(READ_TELEMETRY)
    assert validate_permissions([READ_GRAPH, "context.read"]) == (
        READ_CONTEXT,
        READ_GRAPH,
    )
    with pytest.raises(ValueError, match="WRITE"):
        validate_permissions(["WRITE_GRAPH"])
    with pytest.raises(ValueError, match="unsupported"):
        validate_permissions(["EXECUTE_SHELL"])
    with pytest.raises(ValueError):
        validate_permissions(["  "])
    assert to_sdk_capabilities([READ_GRAPH]) == ("graph.read",)


def test_registry_register_list_get(tmp_path: Path) -> None:
    reg = MarketplaceRegistry(root=tmp_path / "mkt")
    m = _manifest()
    reg.register(m)
    assert reg.get_plugin("demo-plugin") is not None
    assert len(reg.list_plugins()) == 1
    assert reg.index().sdk_version == "5.0.0"
    assert reg.unregister("demo-plugin") is True
    assert reg.unregister("missing") is False
    assert reg.get_plugin("demo-plugin") is None
    # empty / corrupt files
    reg.catalog_path.write_text("[]\n", encoding="utf-8")
    reg.reload()
    assert reg.list_plugins() == ()
    reg.catalog_path.write_text(
        json.dumps(
            {
                "plugins": [
                    {
                        "id": "z",
                        "name": "Z",
                        "version": "1",
                        "checksum": "sha256:" + ("0" * 64),
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    reg.reload()
    assert reg.get_plugin("z") is not None


def test_discovery_filters(tmp_path: Path) -> None:
    reg = MarketplaceRegistry(root=tmp_path / "mkt")
    seed_demo_marketplace(reg)
    disco = MarketplaceDiscovery(reg)
    by_cat = disco.search(DiscoveryQuery(category="telemetry"))
    assert any(p.id == "nvidia-intelligence" for p in by_cat)
    by_author = disco.search(DiscoveryQuery(author="NVIDIA"))
    assert by_author and by_author[0].author == "NVIDIA"
    by_sdk = disco.search(DiscoveryQuery(sdk_version="5"))
    assert by_sdk
    installed_only = disco.search(DiscoveryQuery(installed=True))
    assert installed_only
    enabled = disco.search(DiscoveryQuery(enabled=True))
    assert enabled
    disabled = disco.installed(enabled=False)
    assert any(not r.enabled for r in disabled)
    assert len(disco.installed()) >= 1


def test_validator_manifest_and_package(tmp_path: Path) -> None:
    bad = _manifest(sdk_version=">=9.0.0,<10", permissions=(READ_GRAPH,))
    result = validate_manifest(bad)
    assert result.ok is False
    assert any("SDK" in r for r in result.reasons)

    bad_cs = _manifest(checksum="md5:abc")
    assert validate_manifest(bad_cs).ok is False

    ok = validate_manifest(_manifest())
    assert ok.ok is True

    missing = validate_package(tmp_path / "nope")
    assert missing.ok is False

    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "plugin.py").write_text("PLUGIN = None\n", encoding="utf-8")
    checksum = compute_checksum(pkg)
    meta = _manifest(id="pkg", checksum=checksum).to_dict()
    (pkg / "marketplace.json").write_text(json.dumps(meta), encoding="utf-8")
    # checksum in meta includes marketplace.json — validator allows excluding it
    # Recompute excluding marketplace.json and rewrite
    from aetheros.marketplace.validator import compute_checksum_excluding

    excl = compute_checksum_excluding(pkg, exclude_names={"marketplace.json"})
    meta["checksum"] = excl
    (pkg / "marketplace.json").write_text(json.dumps(meta), encoding="utf-8")
    verified = validate_package(pkg)
    assert verified.ok is True
    assert verified.manifest is not None

    # mismatch against expected catalog entry
    expected = _manifest(id="pkg", checksum="sha256:" + ("9" * 64))
    mismatch = validate_package(pkg, expected=expected)
    assert mismatch.ok is False


def test_validator_bridges_plugin_yaml(tmp_path: Path) -> None:
    pkg = tmp_path / "hello"
    pkg.mkdir()
    (pkg / "plugin.yaml").write_text(
        "\n".join(
            [
                "id: bridge-me",
                "name: Bridge Me",
                "version: 0.1.0",
                "author: Tests",
                "description: bridge",
                'sdk: ">=5.0.0,<6"',
                "capabilities:",
                "  - graph.read",
                "  - context.read",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (pkg / "plugin.py").write_text("# noop\n", encoding="utf-8")
    result = validate_package(pkg)
    assert result.ok is True
    assert result.manifest is not None
    assert result.manifest.id == "bridge-me"
    assert READ_GRAPH in result.manifest.permissions


def test_installer_lifecycle(tmp_path: Path) -> None:
    reg = MarketplaceRegistry(root=tmp_path / "mkt")
    installer = MarketplaceInstaller(registry=reg, install_root=tmp_path / "installed")

    pkg = tmp_path / "src" / "demo-plugin"
    pkg.mkdir(parents=True)
    (pkg / "plugin.py").write_text("print('hi')\n", encoding="utf-8")
    (pkg / "placeholder").write_text("x", encoding="utf-8")
    from aetheros.marketplace.validator import compute_checksum_excluding

    excl = compute_checksum_excluding(pkg, exclude_names={"marketplace.json"})
    manifest = _manifest(id="demo-plugin", checksum=excl)
    (pkg / "marketplace.json").write_text(
        json.dumps(manifest.to_dict()), encoding="utf-8"
    )
    reg.register(manifest)

    record = installer.install(pkg)
    assert record.enabled is True
    assert (tmp_path / "installed" / "demo-plugin").is_dir()

    # Reinstall over existing target
    record2 = installer.install(pkg, enable=False)
    assert record2.enabled is False

    assert installer.enable("demo-plugin").enabled is True
    assert installer.disable("demo-plugin").enabled is False
    assert installer.uninstall("demo-plugin") is True
    assert installer.uninstall("demo-plugin") is False
    with pytest.raises(KeyError):
        installer.enable("missing")
    with pytest.raises(KeyError):
        installer.disable("missing")

    # Single-file install path
    single = tmp_path / "solo.py"
    single.write_text("# plugin\n", encoding="utf-8")
    # Reject: no marketplace metadata
    with pytest.raises(ValueError):
        installer.install(single)

    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "marketplace.json").write_text(
        json.dumps(
            _manifest(
                id="bad",
                sdk_version=">=9.0.0,<10",
                checksum="sha256:" + ("0" * 64),
            ).to_dict()
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="rejected"):
        installer.install(bad)


def test_updater_recommendations(tmp_path: Path) -> None:
    reg = MarketplaceRegistry(root=tmp_path / "mkt")
    old = _manifest(id="hello-insight", version="0.1.0")
    new = _manifest(id="hello-insight", version="0.2.0")
    reg.register(new)
    reg.put_installed(
        InstalledPlugin(
            manifest=old,
            enabled=True,
            installed_at=datetime.now(UTC),
        )
    )
    updater = MarketplaceUpdater(reg)
    tip = updater.check("hello-insight")
    assert tip.update_available is True
    assert tip.available_version == "0.2.0"
    assert is_newer("1.2.0", "1.1.9")
    assert not is_newer("1.0.0", "1.0.0")

    tips = updater.mark_update_flags()
    assert any(t.update_available for t in tips)
    assert reg.get_installed("hello-insight") is not None
    assert reg.get_installed("hello-insight").update_available is True

    gone = updater.check("nope")
    assert gone.reason == "not installed"

    # deprecated when removed from catalog
    only = _manifest(id="orphan", version="1.0.0")
    reg.put_installed(
        InstalledPlugin(manifest=only, enabled=True, installed_at=datetime.now(UTC))
    )
    dep = updater.check("orphan")
    assert dep.deprecated is True

    # incompatible newer
    reg.register(
        _manifest(id="hello-insight", version="9.0.0", sdk_version=">=9.0.0,<10")
    )
    tip2 = updater.check("hello-insight")
    assert tip2.update_available is True
    assert tip2.sdk_compatible is False


def test_formatter_views(tmp_path: Path) -> None:
    reg = MarketplaceRegistry(root=tmp_path / "mkt")
    seed_demo_marketplace(reg)
    updates = MarketplaceUpdater(reg).check_all()
    catalog = reg.list_plugins()
    installed = reg.list_installed()
    selected = reg.get_plugin("nvidia-intelligence")

    idle = _print(MarketplacePanel())
    assert "idle" in idle.lower() or "MARKETPLACE" in idle

    market = _print(
        MarketplacePanel(
            catalog=catalog,
            installed=installed,
            updates=updates,
            selected=selected,
            view="marketplace",
        )
    )
    assert "AETHEROS MARKETPLACE" in market
    assert "NVIDIA Intelligence" in market
    assert "READ_GRAPH" in market

    for view in ("installed", "updates", "permissions", "details"):
        text = _print(
            MarketplacePanel(
                catalog=catalog,
                installed=installed,
                updates=updates,
                selected=selected,
                view=view,
            )
        )
        assert "AETHEROS MARKETPLACE" in text

    empty_updates = _print(
        MarketplacePanel(
            catalog=catalog, installed=installed, updates=(), view="updates"
        )
    )
    assert "none" in empty_updates.lower() or "Updates" in empty_updates


def test_demo_catalog_and_seed(tmp_path: Path) -> None:
    assert any(p.name == "NVIDIA Intelligence" for p in demo_catalog())
    reg = MarketplaceRegistry(root=tmp_path / "mkt")
    seed_demo_marketplace(reg)
    assert len(reg.list_installed()) >= 3
    assert isinstance(updater_check := MarketplaceUpdater(reg).check_all(), tuple)
    assert updater_check


def test_file_checksum_helper(tmp_path: Path) -> None:
    f = tmp_path / "one.txt"
    f.write_text("abc", encoding="utf-8")
    digest = compute_checksum(f)
    assert digest.startswith("sha256:")


def test_registry_installed_persistence(tmp_path: Path) -> None:
    reg = MarketplaceRegistry(root=tmp_path / "mkt")
    m = _manifest()
    reg.register(m)
    reg.put_installed(
        InstalledPlugin(
            manifest=m,
            enabled=True,
            installed_at=datetime.now(UTC),
            install_path=str(tmp_path / "x"),
        )
    )
    assert reg.get_installed("demo-plugin") is not None
    assert reg.remove_installed("demo-plugin") is True
    assert reg.remove_installed("demo-plugin") is False
    # corrupt installed file
    reg.installed_path.write_text("[]\n", encoding="utf-8")
    reg.reload()
    assert reg.list_installed() == ()
    reg.installed_path.write_text(
        json.dumps(
            {
                "installed": [
                    {
                        "manifest": m.to_dict(),
                        "enabled": False,
                        "installed_at": datetime.now(UTC).isoformat(),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    reg.reload()
    assert reg.get_installed("demo-plugin") is not None
    assert reg.get_installed("demo-plugin").enabled is False


def test_formatter_edge_branches() -> None:
    m = _manifest(permissions=())
    text = _print(
        MarketplacePanel(
            catalog=(m,), installed=(), updates=(), selected=m, view="marketplace"
        )
    )
    assert "none" in text.lower() or "Permissions" in text
    text2 = _print(
        MarketplacePanel(
            catalog=(m,),
            installed=(),
            updates=(
                UpdateRecommendation(
                    plugin_id="demo-plugin",
                    current_version="1.0.0",
                    available_version="1.1.0",
                    update_available=True,
                    sdk_compatible=True,
                    deprecated=False,
                    reason="newer",
                ),
            ),
            view="updates",
        )
    )
    assert "demo-plugin" in text2
    text3 = _print(MarketplacePanel(catalog=(), installed=(), view="details"))
    assert "idle" in text3.lower()
    # details from installed
    rec = InstalledPlugin(
        manifest=m,
        enabled=True,
        installed_at=datetime.now(UTC),
    )
    text4 = _print(
        MarketplacePanel(catalog=(), installed=(rec,), view="plugin details")
    )
    assert "Demo Plugin" in text4
    text5 = _print(MarketplacePanel(catalog=(m,), installed=(), view="installed"))
    assert "none" in text5.lower()

    # details with catalog only (no selected)
    text6 = _print(MarketplacePanel(catalog=(m,), installed=(), view="details"))
    assert "Demo Plugin" in text6


def test_discovery_sdk_substring_and_empty_token() -> None:
    from aetheros.marketplace.discovery import _sdk_major

    assert _sdk_major("") is None
    assert _sdk_major(">=5.0.0,<6") == 5
    assert normalize_permission("") == ""


def test_models_empty_fields() -> None:
    with pytest.raises(ValueError):
        _manifest(name="")
    with pytest.raises(ValueError):
        _manifest(version="")
    with pytest.raises(ValueError):
        _manifest(checksum="")
    # permissions as string
    m = PluginManifest.from_dict(
        {
            "id": "s",
            "name": "S",
            "version": "1",
            "checksum": "sha256:" + ("2" * 64),
            "permissions": "READ_GRAPH",
        }
    )
    assert m.permissions == (READ_GRAPH,)


def test_updater_compatible_current(tmp_path: Path) -> None:
    reg = MarketplaceRegistry(root=tmp_path / "mkt")
    m = _manifest(version="1.0.0")
    reg.register(m)
    reg.put_installed(
        InstalledPlugin(manifest=m, enabled=True, installed_at=datetime.now(UTC))
    )
    tip = MarketplaceUpdater(reg).check("demo-plugin")
    assert tip.reason == "up to date"

    # installed incompatible without newer catalog
    bad = _manifest(id="old-sdk", version="1.0.0", sdk_version=">=4.0.0,<5")
    reg.register(bad)
    reg.put_installed(
        InstalledPlugin(manifest=bad, enabled=True, installed_at=datetime.now(UTC))
    )
    tip2 = MarketplaceUpdater(reg).check("old-sdk")
    assert tip2.sdk_compatible is False


def test_validate_manifest_permission_failure() -> None:
    # PluginManifest does not validate permissions itself — validator does.
    result = validate_manifest(
        PluginManifest(
            id="w",
            name="W",
            version="1",
            author="a",
            description="d",
            sdk_version=">=5.0.0,<6",
            category="c",
            permissions=("WRITE_GRAPH",),
            checksum="sha256:" + ("3" * 64),
        )
    )
    assert result.ok is False


def test_validate_package_bad_marketplace_json(tmp_path: Path) -> None:
    pkg = tmp_path / "p"
    pkg.mkdir()
    (pkg / "marketplace.json").write_text(
        json.dumps({"id": "", "name": "x", "version": "1", "checksum": "sha256:abc"}),
        encoding="utf-8",
    )
    result = validate_package(pkg)
    assert result.ok is False


def test_validate_package_missing_yaml(tmp_path: Path) -> None:
    pkg = tmp_path / "empty"
    pkg.mkdir()
    (pkg / "readme.txt").write_text("nope", encoding="utf-8")
    assert validate_package(pkg).ok is False


def test_installer_uninstall_with_path(tmp_path: Path) -> None:
    reg = MarketplaceRegistry(root=tmp_path / "mkt")
    installer = MarketplaceInstaller(registry=reg, install_root=tmp_path / "installed")
    target = tmp_path / "installed" / "ghost"
    target.mkdir(parents=True)
    (target / "f").write_text("x", encoding="utf-8")
    m = _manifest(id="ghost")
    reg.register(m)
    reg.put_installed(
        InstalledPlugin(
            manifest=m,
            enabled=True,
            installed_at=datetime.now(UTC),
            install_path=str(target),
        )
    )
    assert installer.uninstall("ghost") is True
    assert not target.exists()
