"""Guardrail: forbid package-level import cycles under aetheros."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_import_cycles import (  # noqa: E402
    mutual_pairs,
    package_edges,
    strongly_connected,
)


def test_no_package_import_cycles() -> None:
    """Critical P1 pairs and any SCC > 1 must stay gone."""

    edges = package_edges(ROOT / "aetheros")
    pairs = mutual_pairs(edges)
    sccs = strongly_connected(edges)
    forbidden = {
        frozenset({"agents", "runtime"}),
        frozenset({"cognition", "reasoning"}),
        frozenset({"decision", "intent"}),
    }
    found = {frozenset(pair) for pair in pairs}
    assert not (found & forbidden), f"forbidden cycles returned: {found & forbidden}"
    assert not pairs, f"mutual package cycles: {pairs}"
    assert not sccs, f"package SCCs: {[sorted(c) for c in sccs]}"
