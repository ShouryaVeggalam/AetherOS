"""Unit tests for AetherOS Infinity (∞)."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from aetheros.infinity import (
    GENERATIONS,
    PIPELINE,
    PRINCIPLES,
    InfinityPanel,
    InfinityRuntime,
)
from aetheros.kernel import KernelIntelligence
from aetheros.policy import PolicyEngine


def test_generations_and_pipeline() -> None:
    """Catalog should include v1–v9 and Infinity with a full pipeline."""

    versions = [g.version for g in GENERATIONS]
    assert versions[0] == "v1"
    assert versions[-1] == "∞"
    assert len(GENERATIONS) == 10
    assert PIPELINE[-1].name == "Human Approval"
    assert "Humans remain in control." in PRINCIPLES


def test_kernel_and_policy_shims() -> None:
    """Compatibility packages should expose userspace-only surfaces."""

    ctx = KernelIntelligence().context()
    assert ctx.status == "userspace-only"
    assert ctx.relation_count >= 1
    assert PolicyEngine is not None


def test_infinity_runtime_and_panel(tmp_path: Path) -> None:
    """InfinityRuntime should report ready layers and render a panel."""

    from aetheros.fabric import FabricRuntime
    from aetheros.genesis import GenesisRuntime
    from aetheros.genesis.knowledge_base import KnowledgeBase
    from aetheros.genesis.theorem_store import TheoremStore

    runtime = InfinityRuntime(
        genesis=GenesisRuntime(
            knowledge=KnowledgeBase(tmp_path / "kb.db"),
            theorems=TheoremStore(tmp_path / "th.db"),
        ),
        fabric=FabricRuntime(knowledge=KnowledgeBase(tmp_path / "kb2.db")),
    )
    report = runtime.observe()
    assert report.generation_count == 10
    assert report.layers_ready == len(report.layers)
    assert "Human-in-the-loop" in report.status
    assert "not an OS" in report.identity.lower() or "not an OS" in report.identity

    console = Console(record=True, width=100)
    console.print(InfinityPanel(report=report))
    text = console.export_text()
    assert "AETHEROS" in text or "Infinity" in text
    assert "Human Approval" in text or "pipeline" in text.lower()


def test_infinity_api(tmp_path: Path) -> None:
    """GET /infinity should return generation and layer status JSON."""

    from fastapi.testclient import TestClient

    from aetheros.api import create_app

    client = TestClient(create_app(memory_db=tmp_path / "cog.db"))
    health = client.get("/health").json()
    assert health["version"].startswith("5.")
    payload = client.get("/infinity").json()
    assert payload["generation_count"] == 10
    assert payload["layers_ready"] >= 1
    assert len(payload["pipeline"]) == len(PIPELINE)
    assert payload["generations"][-1]["codename"] == "Infinity"
