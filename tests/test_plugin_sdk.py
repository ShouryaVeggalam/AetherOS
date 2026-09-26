"""Tests for AetherOS v5.0 P1 Plugin SDK (``plugins.sdk``)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from rich.console import Console

from plugins.sdk import (
    SDK_VERSION,
    CapabilityRegistry,
    ContextSnapshot,
    EventBus,
    GraphNodeView,
    GraphSnapshot,
    IntelligencePlugin,
    PluginHostAPI,
    PluginInspector,
    PluginLoader,
    PluginManifest,
    PluginSandbox,
    PluginValidator,
    graph_from_mapping,
    inspect_plugins,
    load_manifest,
    parse_manifest,
    sdk_constraint_allows,
)
from plugins.sdk.manifest import unknown_capabilities
from plugins.sdk.sandbox import SandboxResult

EXAMPLES = Path(__file__).resolve().parents[1] / "plugins" / "examples"


def _print(renderable: object) -> str:
    console = Console(record=True, width=100, force_terminal=True)
    console.print(renderable)
    return console.export_text()


# --- version / manifest ------------------------------------------------------


def test_sdk_version_and_constraints() -> None:
    assert SDK_VERSION.startswith("5.")
    assert sdk_constraint_allows(">=5.0.0,<6")
    assert sdk_constraint_allows("5.x")
    assert sdk_constraint_allows("==5.0.0")
    assert not sdk_constraint_allows(">=6.0.0,<7")
    assert not sdk_constraint_allows("")
    assert unknown_capabilities(("graph.read", "nope")) == ("nope",)


def test_parse_and_load_manifest(tmp_path: Path) -> None:
    raw = """
id: demo
name: Demo
version: 1.2.3
author: QA
description: test
sdk: ">=5.0.0,<6"
capabilities: [graph.read, context.read]
events: telemetry.tick
enabled: true
"""
    manifest = parse_manifest(raw)
    assert manifest.id == "demo"
    assert "graph.read" in manifest.capabilities
    assert manifest.events == ("telemetry.tick",)
    path = tmp_path / "plugin.yaml"
    path.write_text(raw, encoding="utf-8")
    assert load_manifest(path).name == "Demo"
    with pytest.raises(ValueError):
        PluginManifest(id=" ", name="n", version="1", author="a", description="d")
    with pytest.raises(ValueError):
        parse_manifest("[]")
    with pytest.raises(ValueError):
        parse_manifest(": : bad: yaml: [[")


# --- capabilities / events / context -----------------------------------------


def test_capability_registry() -> None:
    reg = CapabilityRegistry()
    reg.register("graph.read")
    reg.register_many(("context.read", "events.subscribe"))
    assert reg.has("graph.read")
    reg.require("graph.read")
    with pytest.raises(PermissionError):
        reg.require("telemetry.read")
    with pytest.raises(ValueError):
        reg.register("not.real")
    with pytest.raises(ValueError):
        from plugins.sdk.capabilities import CapabilityGrant

        CapabilityGrant(name=" ")


def test_event_bus() -> None:
    bus = EventBus()
    seen: list[str] = []

    def handler(event: object) -> None:
        seen.append(getattr(event, "topic", ""))

    bus.subscribe("telemetry.tick", handler)
    bus.publish("telemetry.tick", {"cpu": 1}, now=datetime(2026, 9, 26, tzinfo=UTC))
    assert seen == ["telemetry.tick"]
    assert bus.topics() == ("telemetry.tick",)
    assert len(bus.history(limit=1)) == 1
    assert bus.history(limit=0) == ()
    bus.unsubscribe("telemetry.tick", handler)
    with pytest.raises(ValueError):
        bus.subscribe(" ", handler)
    with pytest.raises(ValueError):
        from plugins.sdk.events import PluginEvent

        PluginEvent(topic=" ", payload={}, emitted_at=datetime.now(UTC))


def test_graph_and_context_api() -> None:
    snap = graph_from_mapping(
        {
            "nodes": [
                {"id": "cpu", "name": "CPU", "kind": "CPU", "attributes": {"p": "1"}},
                {"id": "", "name": "skip", "kind": "X"},
            ],
            "edges": [
                {"source": "cpu", "target": "mem", "relation": "USES", "weight": 0.5}
            ],
        }
    )
    assert snap.node_ids() == ("cpu",)
    assert snap.nodes_of_kind("cpu")[0].name == "CPU"
    api = PluginHostAPI()
    api.capabilities.register("graph.read")
    api.capabilities.register("context.read")
    api.graph.set_snapshot(snap)
    api.context.set_snapshot(
        ContextSnapshot(intent="Coding", labels=(("zone", "lab"),))
    )
    graph = api.read_graph()
    assert graph.get_node("cpu") is not None
    assert graph.get_node("missing") is None
    assert api.read_context().label("zone") == "lab"
    assert api.read_context().snapshot().as_dict()["intent"] == "Coding"


# --- sandbox / validator / loader --------------------------------------------


def test_sandbox_rejects_forbidden(tmp_path: Path) -> None:
    sandbox = PluginSandbox()
    empty = tmp_path / "empty"
    empty.mkdir()
    assert sandbox.validate_path(empty).safe is False

    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "plugin.py").write_text("import subprocess\n", encoding="utf-8")
    result = sandbox.validate_path(bad)
    assert result.safe is False
    assert any("subprocess" in f for f in result.findings)

    evil = tmp_path / "evil"
    evil.mkdir()
    (evil / "plugin.py").write_text("eval('1')\n", encoding="utf-8")
    assert sandbox.validate_path(evil).safe is False

    os_bad = tmp_path / "osbad"
    os_bad.mkdir()
    (os_bad / "plugin.py").write_text("import os\nos.system('x')\n", encoding="utf-8")
    assert sandbox.validate_path(os_bad).safe is False


def test_validator_and_example_loader() -> None:
    validator = PluginValidator()
    example = EXAMPLES / "hello_insight"
    result = validator.validate_directory(example)
    assert result.ok is True
    assert result.manifest is not None
    assert result.manifest.id == "hello-insight"

    missing = validator.validate_directory(EXAMPLES / "does-not-exist")
    assert missing.ok is False

    loader = PluginLoader()
    api = PluginHostAPI()
    api.graph.set_snapshot(GraphSnapshot(nodes=(GraphNodeView("cpu", "CPU", "CPU"),)))
    api.context.set_snapshot(ContextSnapshot(intent="Coding"))
    loaded = loader.load_plugin(example, api=api)
    assert not isinstance(loaded, type(None))
    from plugins.sdk import LoadedPlugin

    assert isinstance(loaded, LoadedPlugin)
    assert loaded.api.notes()
    assert loaded.api.meta()["graph_nodes"] == 1
    # Event subscription from manifest
    loaded.api.events.publish("telemetry.tick", {"ok": True})

    discovered = loader.discover(EXAMPLES)
    assert any(p.name == "hello_insight" for p in discovered)


def test_loader_rejects_invalid(tmp_path: Path) -> None:
    loader = PluginLoader()
    # No manifest
    bare = tmp_path / "bare"
    bare.mkdir()
    (bare / "plugin.py").write_text(
        "from plugins.sdk import IntelligencePlugin\n"
        "class P(IntelligencePlugin):\n"
        "    def register(self, api): pass\n"
        "PLUGIN = P()\n",
        encoding="utf-8",
    )
    rejected = loader.load_plugin(bare)
    from plugins.sdk import RejectedPlugin

    assert isinstance(rejected, RejectedPlugin)

    # Manifest with unknown capability
    bad_cap = tmp_path / "badcap"
    bad_cap.mkdir()
    (bad_cap / "plugin.yaml").write_text(
        "id: x\nname: X\nversion: 1\nauthor: a\ndescription: d\n"
        "sdk: '>=5.0.0,<6'\ncapabilities: [not.a.cap]\n",
        encoding="utf-8",
    )
    (bad_cap / "plugin.py").write_text(
        "from plugins.sdk import IntelligencePlugin\n"
        "class P(IntelligencePlugin):\n"
        "    def register(self, api): pass\n"
        "PLUGIN = P()\n",
        encoding="utf-8",
    )
    assert isinstance(loader.load_plugin(bad_cap), RejectedPlugin)


def test_inspector_rich() -> None:
    loader = PluginLoader()
    results = [loader.load_plugin(p) for p in loader.discover(EXAMPLES)]
    inspector = inspect_plugins(results)
    text = _print(inspector)
    assert "PLUGIN SDK" in text
    assert "hello-insight" in text or "verified" in text
    empty = _print(PluginInspector())
    assert "no plugins" in empty


def test_host_api_permission_gates() -> None:
    api = PluginHostAPI()
    with pytest.raises(PermissionError):
        api.read_graph()
    with pytest.raises(PermissionError):
        api.subscribe("x", lambda e: None)
    api.capabilities.register("events.subscribe")
    api.subscribe("x", lambda e: None)
    api.contribute_note("  hi  ")
    assert api.notes() == ("hi",)
    assert "T" in api.stamp()


class _Tiny(IntelligencePlugin):
    def register(self, api: PluginHostAPI) -> None:
        api.contribute_note("tiny")


def test_loader_edge_cases(tmp_path: Path) -> None:
    loader = PluginLoader()
    assert loader.discover(tmp_path / "missing") == ()

    # Sandbox failure after valid manifest
    unsafe = tmp_path / "unsafe"
    unsafe.mkdir()
    (unsafe / "plugin.yaml").write_text(
        "id: unsafe\nname: U\nversion: 1\nauthor: a\ndescription: d\n"
        "sdk: '>=5.0.0,<6'\ncapabilities: []\n",
        encoding="utf-8",
    )
    (unsafe / "plugin.py").write_text("import socket\n", encoding="utf-8")
    from plugins.sdk import RejectedPlugin

    assert isinstance(loader.load_plugin(unsafe), RejectedPlugin)

    # Missing entry file
    noentry = tmp_path / "noentry"
    noentry.mkdir()
    (noentry / "plugin.yaml").write_text(
        "id: noentry\nname: N\nversion: 1\nauthor: a\ndescription: d\n"
        "sdk: '>=5.0.0,<6'\nentry: missing.py\ncapabilities: []\n",
        encoding="utf-8",
    )
    assert isinstance(loader.load_plugin(noentry), RejectedPlugin)

    # Import exposes nothing
    empty_mod = tmp_path / "emptymod"
    empty_mod.mkdir()
    (empty_mod / "plugin.yaml").write_text(
        "id: empty\nname: E\nversion: 1\nauthor: a\ndescription: d\n"
        "sdk: '>=5.0.0,<6'\ncapabilities: []\n",
        encoding="utf-8",
    )
    (empty_mod / "plugin.py").write_text("VALUE = 1\n", encoding="utf-8")
    assert isinstance(loader.load_plugin(empty_mod), RejectedPlugin)

    # register() raises
    boom = tmp_path / "boom"
    boom.mkdir()
    (boom / "plugin.yaml").write_text(
        "id: boom\nname: B\nversion: 1\nauthor: a\ndescription: d\n"
        "sdk: '>=5.0.0,<6'\ncapabilities: []\n",
        encoding="utf-8",
    )
    (boom / "plugin.py").write_text(
        "from plugins.sdk import IntelligencePlugin\n"
        "class Boom(IntelligencePlugin):\n"
        "    def register(self, api):\n"
        "        raise RuntimeError('nope')\n"
        "PLUGIN = Boom()\n",
        encoding="utf-8",
    )
    assert isinstance(loader.load_plugin(boom), RejectedPlugin)

    # Incompatible sdk constraint
    old = tmp_path / "old"
    old.mkdir()
    (old / "plugin.yaml").write_text(
        "id: old\nname: O\nversion: 1\nauthor: a\ndescription: d\n"
        "sdk: '>=6.0.0,<7'\ncapabilities: []\n",
        encoding="utf-8",
    )
    (old / "plugin.py").write_text(
        "from plugins.sdk import IntelligencePlugin\n"
        "class P(IntelligencePlugin):\n"
        "    def register(self, api): pass\n"
        "PLUGIN = P()\n",
        encoding="utf-8",
    )
    assert isinstance(loader.load_plugin(old), RejectedPlugin)


def test_sandbox_extra_paths(tmp_path: Path) -> None:
    sandbox = PluginSandbox()
    syn = tmp_path / "syn"
    syn.mkdir()
    (syn / "plugin.py").write_text("def (\n", encoding="utf-8")
    assert sandbox.validate_path(syn).safe is False

    attr = tmp_path / "attr"
    attr.mkdir()
    (attr / "plugin.py").write_text("import os\nx = os.system\n", encoding="utf-8")
    assert sandbox.validate_path(attr).safe is False

    os_from = tmp_path / "osfrom"
    os_from.mkdir()
    (os_from / "plugin.py").write_text("from os import system\n", encoding="utf-8")
    assert sandbox.validate_path(os_from).safe is False


def test_inspector_with_rejection(tmp_path: Path) -> None:
    from plugins.sdk import RejectedPlugin

    rejected = RejectedPlugin(
        path=tmp_path / "x",
        reason="boom",
        sandbox=SandboxResult(safe=False, reason="nope", findings=("x",)),
    )
    text = _print(inspect_plugins([rejected]))
    assert "rejected" in text


def test_manifest_validation_edges() -> None:
    with pytest.raises(ValueError):
        PluginManifest(id="x", name=" ", version="1", author="a", description="d")
    with pytest.raises(ValueError):
        PluginManifest(id="x", name="n", version=" ", author="a", description="d")
    m = parse_manifest(
        "id: z\nname: Z\nversion: 1\nauthor: a\ndescription: d\n"
        "capabilities: graph.read\n"
    )
    assert m.capabilities == ("graph.read",)
    assert sdk_constraint_allows("5")
    assert sdk_constraint_allows("5.1.0")


def test_context_attr_list_and_api_require() -> None:
    snap = graph_from_mapping(
        {
            "nodes": [
                {
                    "id": "n1",
                    "name": "N",
                    "kind": "Host",
                    "attributes": (("k", "v"),),
                }
            ],
            "edges": [],
        }
    )
    assert snap.nodes[0].attributes == (("k", "v"),)
    api = PluginHostAPI()
    api.capabilities.register("graph.read")
    api.require("graph.read")
    api.graph.set_snapshot(snap)
    assert api.graph.list_nodes()[0].id == "n1"
    assert api.graph.list_edges() == ()
    p = _Tiny()
    assert p.on_event(object()) is None


def test_custom_plugin_class_extract(tmp_path: Path) -> None:
    root = tmp_path / "tiny"
    root.mkdir()
    (root / "plugin.yaml").write_text(
        "id: tiny\nname: Tiny\nversion: 0.0.1\nauthor: t\n"
        "description: t\nsdk: '>=5.0.0,<6'\ncapabilities: []\n",
        encoding="utf-8",
    )
    (root / "plugin.py").write_text(
        "from plugins.sdk import IntelligencePlugin\n"
        "class Tiny(IntelligencePlugin):\n"
        "    def register(self, api):\n"
        "        api.contribute_note('tiny')\n"
        "def create_plugin():\n"
        "    return Tiny()\n",
        encoding="utf-8",
    )
    loaded = PluginLoader().load_plugin(root)
    from plugins.sdk import LoadedPlugin

    assert isinstance(loaded, LoadedPlugin)
    assert loaded.api.notes() == ("tiny",)
