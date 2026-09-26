"""Public API v1 — Resource / World graph (read-only).

Exposes existing WorldGraph sample JSON. Never mutates graph stores.
"""

from __future__ import annotations

from fastapi import APIRouter

from aetheros.api.schemas import V1GraphEdge, V1GraphNode, V1GraphResponse
from aetheros.horizon import WorldGraph

router = APIRouter(tags=["public-api-v1"])


@router.get("/graph", response_model=V1GraphResponse)
def get_graph() -> V1GraphResponse:
    """Return a read-only sample world / resource graph projection."""

    raw = WorldGraph().to_dict()
    nodes_raw = raw.get("nodes") or raw.get("census", {}).get("nodes") or []
    edges_raw = raw.get("edges") or []

    # WorldGraph.to_dict may nest differently — normalize best-effort.
    if not isinstance(nodes_raw, list):
        # Flatten region/node listings when present.
        nodes_raw = []
        for key in ("regions", "datacenters", "clusters", "sample_nodes"):
            block = raw.get(key)
            if isinstance(block, list):
                for item in block:
                    if isinstance(item, dict):
                        nodes_raw.append(item)

    nodes: list[V1GraphNode] = []
    for item in nodes_raw:
        if not isinstance(item, dict):
            continue
        node_id = str(item.get("id") or item.get("node_id") or "")
        if not node_id:
            continue
        attrs = item.get("attributes") or {}
        if not isinstance(attrs, dict):
            attrs = {}
        nodes.append(
            V1GraphNode(
                id=node_id,
                name=str(item.get("name") or node_id),
                kind=str(item.get("kind") or item.get("type") or "Node"),
                attributes={str(k): str(v) for k, v in attrs.items()},
            )
        )

    edges: list[V1GraphEdge] = []
    for item in edges_raw:
        if not isinstance(item, dict):
            continue
        edges.append(
            V1GraphEdge(
                source=str(item.get("source") or item.get("source_id") or ""),
                target=str(item.get("target") or item.get("target_id") or ""),
                relation=str(item.get("relation") or "RELATED"),
                weight=float(item.get("weight") or 1.0),
            )
        )

    # Guarantee a minimal graph when sample is census-only.
    if not nodes:
        census = raw.get("census") if isinstance(raw.get("census"), dict) else {}
        for kind, count_key in (
            ("Region", "regions"),
            ("Datacenter", "datacenters"),
            ("Cluster", "clusters"),
            ("Node", "nodes"),
        ):
            raw_count = census.get(count_key)
            if not isinstance(raw_count, (int, float)):
                candidate = raw.get(count_key)
                raw_count = candidate if isinstance(candidate, (int, float)) else 0
            count = int(raw_count)
            for i in range(min(count, 3)):
                nid = f"{kind.lower()}-{i+1}"
                nodes.append(V1GraphNode(id=nid, name=nid, kind=kind))

    return V1GraphResponse(
        nodes=nodes,
        edges=edges,
        node_count=len(nodes),
        edge_count=len(edges),
    )
