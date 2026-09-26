"""Atlas Tree — Rich Tree helper for topology hierarchy rendering.

Presentation only. Builds trees from label paths; never queries live hosts.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from rich.console import RenderableType
from rich.text import Text
from rich.tree import Tree


@dataclass(frozen=True, slots=True)
class TreeNodeSpec:
    """One node in a presentation tree (label + optional children)."""

    label: str
    style: str = "bright_white"
    children: tuple[TreeNodeSpec, ...] = ()

    def __post_init__(self) -> None:
        if not self.label.strip():
            raise ValueError("label must be non-empty")


@dataclass(frozen=True, slots=True)
class AtlasTree:
    """Immutable Rich Tree built from nested ``TreeNodeSpec`` values."""

    root_label: str
    children: tuple[TreeNodeSpec, ...] = ()
    root_style: str = "bold bright_green"

    def __post_init__(self) -> None:
        if not self.root_label.strip():
            raise ValueError("root_label must be non-empty")

    def __rich__(self) -> RenderableType:
        tree = Tree(Text(self.root_label, style=self.root_style))
        for child in self.children:
            _add(tree, child)
        return tree


def _add(parent: Tree, node: TreeNodeSpec) -> None:
    branch = parent.add(Text(node.label, style=node.style))
    for child in node.children:
        _add(branch, child)


def tree_from_paths(
    root_label: str,
    paths: Sequence[Sequence[str]],
    *,
    root_style: str = "bold bright_green",
) -> AtlasTree:
    """Build an ``AtlasTree`` from path tuples (region → … → node)."""

    # Nested dict of label → children dict.
    nest: dict[str, dict] = {}
    for path in paths:
        cursor = nest
        for part in path:
            label = str(part).strip()
            if not label:
                continue
            cursor = cursor.setdefault(label, {})

    def _walk(mapping: dict[str, dict]) -> tuple[TreeNodeSpec, ...]:
        out: list[TreeNodeSpec] = []
        for label, kids in mapping.items():
            out.append(TreeNodeSpec(label=label, children=_walk(kids)))
        return tuple(out)

    return AtlasTree(
        root_label=root_label,
        children=_walk(nest),
        root_style=root_style,
    )
