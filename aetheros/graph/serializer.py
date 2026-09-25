"""Resource Graph serialization — versioned JSON only (no pickle)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from aetheros.graph.models import (
    EDGE_RELATIONS,
    NODE_TYPES,
    RESOURCE_GRAPH_SCHEMA,
    EdgeRelation,
    NodeType,
    ResourceEdge,
    ResourceGraph,
    ResourceNode,
)

SUPPORTED_SCHEMAS: frozenset[str] = frozenset({RESOURCE_GRAPH_SCHEMA})


def to_dict(graph: ResourceGraph) -> dict[str, Any]:
    """Export a ResourceGraph to a JSON-ready dictionary."""

    return {
        "schema_version": graph.schema_version,
        "nodes": [
            {
                "id": node.id,
                "type": node.type,
                "name": node.name,
                "metadata": dict(node.metadata),
                "created_at": node.created_at.isoformat(),
            }
            for node in graph.nodes
        ],
        "edges": [
            {
                "source": edge.source,
                "target": edge.target,
                "relationship": edge.relationship,
                "weight": edge.weight,
            }
            for edge in graph.edges
        ],
    }


def from_dict(payload: dict[str, Any]) -> ResourceGraph:
    """Import a ResourceGraph from a dictionary.

    Raises:
        ValueError: Unsupported schema or malformed payload.
    """

    version = str(payload.get("schema_version", ""))
    if version not in SUPPORTED_SCHEMAS:
        raise ValueError(f"Unsupported ResourceGraph schema '{version}'")
    nodes = tuple(_parse_node(item) for item in payload.get("nodes", ()))
    edges = tuple(_parse_edge(item) for item in payload.get("edges", ()))
    return ResourceGraph(nodes=nodes, edges=edges, schema_version=version)


def dumps(graph: ResourceGraph, *, indent: int | None = 2) -> str:
    """Serialize a ResourceGraph to a JSON string."""

    return json.dumps(to_dict(graph), indent=indent, sort_keys=True)


def loads(text: str) -> ResourceGraph:
    """Deserialize a ResourceGraph from a JSON string."""

    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("ResourceGraph JSON must be an object")
    return from_dict(payload)


def dump_path(graph: ResourceGraph, path: Path | str) -> Path:
    """Write JSON to ``path`` and return the normalized path."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dumps(graph), encoding="utf-8")
    return target


def load_path(path: Path | str) -> ResourceGraph:
    """Read a ResourceGraph JSON document from disk."""

    return loads(Path(path).read_text(encoding="utf-8"))


def _parse_node(item: dict[str, Any]) -> ResourceNode:
    """Parse one node object."""

    metadata_raw = item.get("metadata") or {}
    if not isinstance(metadata_raw, dict):
        raise ValueError("node metadata must be an object")
    metadata = tuple((str(key), str(value)) for key, value in metadata_raw.items())
    created = datetime.fromisoformat(str(item["created_at"]))
    node_type = str(item["type"])
    if node_type not in NODE_TYPES:
        raise ValueError(f"Unknown node type '{node_type}'")
    return ResourceNode(
        id=str(item["id"]),
        type=cast(NodeType, node_type),
        name=str(item["name"]),
        metadata=metadata,
        created_at=created,
    )


def _parse_edge(item: dict[str, Any]) -> ResourceEdge:
    """Parse one edge object."""

    relation = str(item["relationship"])
    if relation not in EDGE_RELATIONS:
        raise ValueError(f"Unknown edge relationship '{relation}'")
    return ResourceEdge(
        source=str(item["source"]),
        target=str(item["target"]),
        relationship=cast(EdgeRelation, relation),
        weight=float(item["weight"]),
    )
