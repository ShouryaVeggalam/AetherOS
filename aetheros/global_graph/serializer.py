"""JSON serializer for Global Knowledge Graph (no pickle).

Versioned schema + deterministic content hashing.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from aetheros.global_graph.evidence import EvidenceIndex
from aetheros.global_graph.models import GLOBAL_GRAPH_SCHEMA, GlobalKnowledgeGraph


def dumps_canonical(payload: dict[str, Any]) -> str:
    """Encode a mapping as canonical UTF-8 JSON (sorted keys)."""

    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def graph_hash(graph: GlobalKnowledgeGraph) -> str:
    """Deterministic sha256 of nodes + edges (ids and relations only)."""

    stable = {
        "schema_version": graph.schema_version or GLOBAL_GRAPH_SCHEMA,
        "nodes": sorted(
            ({"id": n.id, "type": n.type, "name": n.name} for n in graph.nodes),
            key=lambda d: d["id"],
        ),
        "edges": sorted(
            (
                {
                    "source": e.source,
                    "target": e.target,
                    "relationship": e.relationship,
                    "confidence": e.confidence,
                    "evidence_count": e.evidence_count,
                }
                for e in graph.edges
            ),
            key=lambda d: (d["source"], d["target"], d["relationship"]),
        ),
    }
    digest = hashlib.sha256(dumps_canonical(stable).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def encode_graph(graph: GlobalKnowledgeGraph) -> str:
    """Serialize graph to canonical JSON text."""

    data = graph.to_dict()
    if not data.get("content_hash"):
        data["content_hash"] = graph_hash(graph)
    return dumps_canonical(data)


def decode_graph(text: str) -> GlobalKnowledgeGraph:
    """Parse a GlobalKnowledgeGraph from JSON text."""

    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("graph JSON must be an object")
    return GlobalKnowledgeGraph.from_dict(data)


def encode_evidence(index: EvidenceIndex) -> str:
    """Serialize an evidence index to canonical JSON."""

    return dumps_canonical(index.to_dict())


def graph_to_json(graph: GlobalKnowledgeGraph, *, indent: int | None = 2) -> str:
    """Pretty or compact JSON export."""

    data = graph.to_dict()
    if not data.get("content_hash"):
        data["content_hash"] = graph_hash(graph)
    if indent is None:
        return dumps_canonical(data)
    return json.dumps(data, indent=indent, sort_keys=True, ensure_ascii=False)
