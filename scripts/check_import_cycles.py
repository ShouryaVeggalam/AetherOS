"""Detect package-level import cycles under ``aetheros``.

Used by CI and ``tests/test_import_cycles.py``. Exit code 1 when any
strongly-connected component of size > 1 is found among top-level packages.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections import defaultdict
from pathlib import Path


def package_edges(root: Path) -> set[tuple[str, str]]:
    """Build directed edges between top-level ``aetheros`` packages."""

    edges: set[tuple[str, str]] = set()
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(root)
        src = rel.parts[0] if len(rel.parts) > 1 else "_root"
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            modules: list[str] = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            for module in modules:
                if not module.startswith("aetheros."):
                    continue
                parts = module.split(".")
                if len(parts) < 2:
                    continue
                dst = parts[1]
                if src != dst:
                    edges.add((src, dst))
    return edges


def strongly_connected(edges: set[tuple[str, str]]) -> list[frozenset[str]]:
    """Tarjan SCC; return components with more than one package (cycles)."""

    graph: dict[str, set[str]] = defaultdict(set)
    nodes: set[str] = set()
    for src, dst in edges:
        graph[src].add(dst)
        nodes.add(src)
        nodes.add(dst)

    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    components: list[frozenset[str]] = []

    def strongconnect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlink[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for successor in graph.get(node, ()):
            if successor not in indices:
                strongconnect(successor)
                lowlink[node] = min(lowlink[node], lowlink[successor])
            elif successor in on_stack:
                lowlink[node] = min(lowlink[node], indices[successor])
        if lowlink[node] == indices[node]:
            component: set[str] = set()
            while True:
                member = stack.pop()
                on_stack.discard(member)
                component.add(member)
                if member == node:
                    break
            if len(component) > 1:
                components.append(frozenset(component))

    for node in sorted(nodes):
        if node not in indices:
            strongconnect(node)
    return components


def mutual_pairs(edges: set[tuple[str, str]]) -> list[tuple[str, str]]:
    """Return sorted A↔B pairs (both directions present)."""

    pairs: list[tuple[str, str]] = []
    seen: set[frozenset[str]] = set()
    for src, dst in edges:
        if (dst, src) in edges:
            key = frozenset({src, dst})
            if key not in seen:
                seen.add(key)
                pairs.append(tuple(sorted((src, dst))))
    return sorted(pairs)


def main(argv: list[str] | None = None) -> int:
    """CLI entry — print cycles and return non-zero on failure."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "aetheros",
        help="Path to the aetheros package root",
    )
    args = parser.parse_args(argv)
    edges = package_edges(args.root)
    pairs = mutual_pairs(edges)
    sccs = strongly_connected(edges)
    if not pairs and not sccs:
        print("OK: no aetheros package import cycles")
        return 0
    print("FAIL: aetheros package import cycles detected", file=sys.stderr)
    for a, b in pairs:
        print(f"  mutual: {a} <-> {b}", file=sys.stderr)
    for component in sccs:
        print(f"  scc: {' <-> '.join(sorted(component))}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
