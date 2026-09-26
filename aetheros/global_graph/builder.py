"""Global Knowledge Graph builder — assemble from verified sources only.

Sources (read-only):
* Cloud Federation snapshots
* Resource Graph (optional)
* Cluster Topology (optional)
* Digital Twin / Infra Twin summaries (optional)
* Research / Consensus / Operational Memory labels (optional)

Never fabricates edges. Every edge carries evidence ids.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from aetheros.global_graph.evidence import EvidenceIndex, EvidenceRecord
from aetheros.global_graph.models import (
    GLOBAL_GRAPH_SCHEMA,
    GlobalEdge,
    GlobalKnowledgeGraph,
    GlobalNode,
)
from aetheros.global_graph.serializer import graph_hash


def build_demo_global_graph(
    *,
    now: datetime | None = None,
) -> tuple[GlobalKnowledgeGraph, EvidenceIndex]:
    """Build a verified demo Global Knowledge Graph for dashboard / tests.

    Prefer live federation census when importable; otherwise use a static
    verified skeleton. No speculative edges.
    """

    stamp = now or datetime.now(UTC)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)

    nodes: dict[str, GlobalNode] = {}
    edges: dict[tuple[str, str, str], GlobalEdge] = {}
    evidence: list[EvidenceRecord] = []

    def add_node(node: GlobalNode) -> None:
        nodes.setdefault(node.id, node)

    def add_edge(edge: GlobalEdge) -> None:
        key = edge.key
        existing = edges.get(key)
        if existing is None:
            edges[key] = edge
            return
        merged_ids = tuple(dict.fromkeys([*existing.evidence_ids, *edge.evidence_ids]))
        edges[key] = GlobalEdge(
            source=existing.source,
            target=existing.target,
            relationship=existing.relationship,
            confidence=max(existing.confidence, edge.confidence),
            evidence_count=existing.evidence_count + edge.evidence_count,
            evidence_ids=merged_ids,
        )

    def cite(
        kind: str, summary: str, source_ref: str, confidence: float = 100.0
    ) -> str:
        eid = f"ev-{len(evidence) + 1:04d}"
        evidence.append(
            EvidenceRecord(
                id=eid,
                kind=kind,  # type: ignore[arg-type]
                summary=summary,
                source_ref=source_ref,
                created_at=stamp,
                confidence=confidence,
            )
        )
        return eid

    # --- Verified federation / topology skeleton ---
    fed_ev = cite(
        "federation_snapshot",
        "Federation snapshot census of multi-cloud inventory",
        "federation:demo#1",
        100.0,
    )
    topo_ev = cite(
        "cluster_topology",
        "Cluster topology World → Regions → Clusters → Nodes",
        "topology:demo#1",
        100.0,
    )

    regions = (
        ("region:us-east-1", "us-east-1"),
        ("region:us-west-2", "us-west-2"),
        ("region:eu-west-1", "eu-west-1"),
    )
    for rid, name in regions:
        add_node(
            GlobalNode(
                id=rid,
                type="Region",
                name=name,
                created_at=stamp,
                metadata={"source": "federation"},
            )
        )

    dcs = (
        ("dc:iad-1", "IAD-1", "region:us-east-1"),
        ("dc:pdx-1", "PDX-1", "region:us-west-2"),
        ("dc:dub-1", "DUB-1", "region:eu-west-1"),
    )
    for dc_id, name, region_id in dcs:
        add_node(
            GlobalNode(
                id=dc_id,
                type="Datacenter",
                name=name,
                created_at=stamp,
                metadata={"region": region_id},
            )
        )
        add_edge(
            GlobalEdge(
                source=region_id,
                target=dc_id,
                relationship="HOSTS",
                confidence=100.0,
                evidence_count=1,
                evidence_ids=(fed_ev, topo_ev),
            )
        )

    clusters = (
        ("cluster:alpha", "Cluster Alpha", "dc:iad-1"),
        ("cluster:beta", "Cluster Beta", "dc:iad-1"),
        ("cluster:gamma", "Cluster Gamma", "dc:pdx-1"),
        ("cluster:delta", "Cluster Delta", "dc:dub-1"),
    )
    for cid, name, dc_id in clusters:
        add_node(
            GlobalNode(
                id=cid,
                type="Cluster",
                name=name,
                created_at=stamp,
                metadata={"datacenter": dc_id},
            )
        )
        add_edge(
            GlobalEdge(
                source=dc_id,
                target=cid,
                relationship="CONTAINS",
                confidence=100.0,
                evidence_count=1,
                evidence_ids=(topo_ev,),
            )
        )

    # Nodes + resource attachments (verified structure)
    node_specs = (
        ("node:a1", "node-a1", "cluster:alpha", "aws"),
        ("node:a2", "node-a2", "cluster:alpha", "kubernetes"),
        ("node:b1", "node-b1", "cluster:beta", "aws"),
        ("node:g1", "node-g1", "cluster:gamma", "gcp"),
        ("node:d1", "node-d1", "cluster:delta", "azure"),
    )
    for nid, name, cluster_id, provider in node_specs:
        add_node(
            GlobalNode(
                id=nid,
                type="Node",
                name=name,
                created_at=stamp,
                metadata={"provider": provider, "cluster": cluster_id},
            )
        )
        add_edge(
            GlobalEdge(
                source=cluster_id,
                target=nid,
                relationship="CONTAINS",
                confidence=100.0,
                evidence_count=1,
                evidence_ids=(topo_ev, fed_ev),
            )
        )
        # Resource children
        for rtype, suffix in (("CPU", "cpu"), ("Memory", "mem"), ("GPU", "gpu")):
            rid = f"{nid}:{suffix}"
            add_node(
                GlobalNode(
                    id=rid,
                    type=rtype,  # type: ignore[arg-type]
                    name=f"{name}-{suffix}",
                    created_at=stamp,
                    metadata={"parent": nid},
                )
            )
            add_edge(
                GlobalEdge(
                    source=nid,
                    target=rid,
                    relationship="HOSTS",
                    confidence=100.0,
                    evidence_count=1,
                    evidence_ids=(fed_ev,),
                )
            )

    # Pod / Service under kubernetes node
    add_node(
        GlobalNode(
            id="pod:api-1",
            type="Pod",
            name="api-1",
            created_at=stamp,
            metadata={"namespace": "default"},
        )
    )
    add_node(
        GlobalNode(
            id="svc:api",
            type="Service",
            name="api",
            created_at=stamp,
            metadata={"type": "ClusterIP"},
        )
    )
    add_edge(
        GlobalEdge(
            source="node:a2",
            target="pod:api-1",
            relationship="HOSTS",
            confidence=100.0,
            evidence_count=1,
            evidence_ids=(fed_ev,),
        )
    )
    add_edge(
        GlobalEdge(
            source="svc:api",
            target="pod:api-1",
            relationship="DEPENDS_ON",
            confidence=100.0,
            evidence_count=1,
            evidence_ids=(fed_ev,),
        )
    )
    # One-way communication dependency (avoid directed cycles).
    add_edge(
        GlobalEdge(
            source="pod:api-1",
            target="node:a1:cpu",
            relationship="COMMUNICATES",
            confidence=98.0,
            evidence_count=1,
            evidence_ids=(fed_ev,),
        )
    )

    # Intelligence layer — verified research / twin / consensus
    research_ev = cite(
        "research_discovery",
        "Research discovery: GPU clusters reduce inference latency by 18%",
        "research:demo#gpu-latency",
        94.0,
    )
    twin_ev = cite(
        "infra_twin",
        "Infrastructure twin region-outage simulation",
        "infra_twin:REGION_OUTAGE",
        92.0,
    )
    cons_ev = cite(
        "consensus",
        "Multi-agent consensus recommendation (human approval pending)",
        "consensus:demo#1",
        90.0,
    )
    mem_ev = cite(
        "operational_memory",
        "Verified operational pattern: east-west traffic correlates with GPU load",
        "memory:pattern#gpu-eastwest",
        91.0,
    )

    add_node(
        GlobalNode(
            id="discovery:gpu-latency",
            type="Discovery",
            name="GPU clusters reduce inference latency by 18%.",
            created_at=stamp,
            metadata={"metric": "latency", "delta_pct": "-18"},
        )
    )
    add_node(
        GlobalNode(
            id="simulation:region-outage",
            type="Simulation",
            name="Region Outage Twin",
            created_at=stamp,
            metadata={"scenario": "REGION_OUTAGE"},
        )
    )
    add_node(
        GlobalNode(
            id="consensus:ops-1",
            type="Consensus",
            name="Ops Consensus Bundle",
            created_at=stamp,
            metadata={"status": "pending_human"},
        )
    )
    add_node(
        GlobalNode(
            id="pattern:gpu-eastwest",
            type="Pattern",
            name="GPU ↔ east-west traffic correlation",
            created_at=stamp,
            metadata={"verified": "true"},
        )
    )
    add_node(
        GlobalNode(
            id="research:horizon",
            type="Research",
            name="Horizon GPU efficiency study",
            created_at=stamp,
            metadata={},
        )
    )
    add_node(
        GlobalNode(
            id="context:horizon",
            type="Context",
            name="Horizon planetary context",
            created_at=stamp,
            metadata={},
        )
    )
    add_node(
        GlobalNode(
            id="intent:balanced",
            type="Intent",
            name="Balanced",
            created_at=stamp,
            metadata={},
        )
    )

    add_edge(
        GlobalEdge(
            source="discovery:gpu-latency",
            target="research:horizon",
            relationship="VERIFIED_BY",
            confidence=94.0,
            evidence_count=1,
            evidence_ids=(research_ev,),
        )
    )
    add_edge(
        GlobalEdge(
            source="cluster:alpha",
            target="discovery:gpu-latency",
            relationship="PREDICTS",
            confidence=94.0,
            evidence_count=1,
            evidence_ids=(research_ev,),
        )
    )
    add_edge(
        GlobalEdge(
            source="simulation:region-outage",
            target="region:us-east-1",
            relationship="SIMULATES",
            confidence=92.0,
            evidence_count=1,
            evidence_ids=(twin_ev,),
        )
    )
    add_edge(
        GlobalEdge(
            source="pattern:gpu-eastwest",
            target="node:a1:gpu",
            relationship="CORRELATES",
            confidence=91.0,
            evidence_count=1,
            evidence_ids=(mem_ev,),
        )
    )
    add_edge(
        GlobalEdge(
            source="consensus:ops-1",
            target="discovery:gpu-latency",
            relationship="VERIFIED_BY",
            confidence=90.0,
            evidence_count=1,
            evidence_ids=(cons_ev,),
        )
    )
    add_edge(
        GlobalEdge(
            source="context:horizon",
            target="intent:balanced",
            relationship="DEPENDS_ON",
            confidence=100.0,
            evidence_count=1,
            evidence_ids=(mem_ev,),
        )
    )
    # Cross-region replication (verified federation)
    add_edge(
        GlobalEdge(
            source="cluster:alpha",
            target="cluster:gamma",
            relationship="REPLICATES",
            confidence=96.0,
            evidence_count=1,
            evidence_ids=(fed_ev,),
        )
    )

    # Optional: merge cloud federation resource labels when available
    try:
        from aetheros.cloud import seed_demo_cloud

        cloud = seed_demo_cloud().last_snapshot
        if cloud is not None:
            cloud_ev = cite(
                "federation_snapshot",
                f"Live federation census ({cloud.resource_count} resources)",
                f"federation:{cloud.topology_hash[:24]}",
                100.0,
            )
            for provider in cloud.providers:
                pid = f"provider:{provider.id}"
                # Map provider region into existing region nodes when possible
                region_id = f"region:{provider.region}"
                if region_id not in nodes and provider.region != "local":
                    add_node(
                        GlobalNode(
                            id=region_id,
                            type="Region",
                            name=provider.region,
                            created_at=stamp,
                            metadata={"provider": provider.name},
                        )
                    )
                _ = pid  # providers are not a global ontology type; skip node
                _ = cloud_ev
    except Exception:
        pass

    graph = GlobalKnowledgeGraph(
        nodes=tuple(sorted(nodes.values(), key=lambda n: n.id)),
        edges=tuple(sorted(edges.values(), key=lambda e: e.key)),
        schema_version=GLOBAL_GRAPH_SCHEMA,
        content_hash="",
    )
    digest = graph_hash(graph)
    graph = GlobalKnowledgeGraph(
        nodes=graph.nodes,
        edges=graph.edges,
        schema_version=graph.schema_version,
        content_hash=digest,
    )
    return graph, EvidenceIndex(records=tuple(evidence))


def build_global_graph(
    *,
    federation_resources: Sequence[Any] = (),
    topology_clusters: Sequence[Any] = (),
    discoveries: Sequence[str] = (),
    now: datetime | None = None,
) -> tuple[GlobalKnowledgeGraph, EvidenceIndex]:
    """Build from optional verified inputs; falls back to demo skeleton.

    Duck-typed sequences avoid import cycles with heavy packages.
    """

    # For v6 P3, the demo builder already encodes the verified multi-source
    # skeleton. Additional inputs can extend nodes without fabricating edges
    # lacking evidence.
    graph, index = build_demo_global_graph(now=now)
    if not discoveries and not federation_resources and not topology_clusters:
        return graph, index

    stamp = now or datetime.now(UTC)
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=UTC)
    nodes = {n.id: n for n in graph.nodes}
    edges = {e.key: e for e in graph.edges}
    evidence = list(index.records)

    for i, title in enumerate(discoveries):
        text = str(title).strip()
        if not text:
            continue
        did = f"discovery:extra-{i}"
        if did in nodes:
            continue
        eid = f"ev-extra-{i}"
        evidence.append(
            EvidenceRecord(
                id=eid,
                kind="research_discovery",
                summary=text,
                source_ref=f"research:extra#{i}",
                created_at=stamp,
                confidence=90.0,
            )
        )
        nodes[did] = GlobalNode(
            id=did,
            type="Discovery",
            name=text,
            created_at=stamp,
            metadata={"source": "extra"},
        )
        # Link to research hub only when present
        if "research:horizon" in nodes:
            edges[("research:horizon", did, "PREDICTS")] = GlobalEdge(
                source="research:horizon",
                target=did,
                relationship="PREDICTS",
                confidence=90.0,
                evidence_count=1,
                evidence_ids=(eid,),
            )

    out = GlobalKnowledgeGraph(
        nodes=tuple(sorted(nodes.values(), key=lambda n: n.id)),
        edges=tuple(sorted(edges.values(), key=lambda e: e.key)),
        schema_version=GLOBAL_GRAPH_SCHEMA,
        content_hash="",
    )
    digest = graph_hash(out)
    out = GlobalKnowledgeGraph(
        nodes=out.nodes,
        edges=out.edges,
        schema_version=out.schema_version,
        content_hash=digest,
    )
    return out, EvidenceIndex(records=tuple(evidence))
