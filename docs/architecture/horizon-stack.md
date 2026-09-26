# Architecture diagram — Horizon stack (v6)

Layered view of **AetherOS v6 Horizon** as consumed by operators and integrations.
Companion to [platform-stack.md](platform-stack.md) (Nexus) and [generations.md](generations.md).

## Operator → intelligence flow

```mermaid
flowchart TB
    subgraph Surfaces["Operator surfaces"]
      DASH[Rich Dashboard]
      HOR[aetheros-horizon]
      ATLAS[aetheros-atlas]
      API["FastAPI /api/v1"]
      SDK[AetherClient]
    end

    subgraph Horizon["v6 Horizon layer"]
      CLOUD[Cloud Federation]
      ITWIN[Infrastructure Twin]
      GKG[Global Knowledge Graph]
      PLAN[Planetary Scheduler]
      HOBS[Horizon Observatory UI]
    end

    subgraph Nexus["v5 Nexus layer"]
      PLG[Plugin SDK]
      MKT[Marketplace]
      PST[Policy Studio]
      ENT[Enterprise]
    end

    subgraph Distributed["v4 Distributed"]
      FED[Federation Protocol]
      TOP[Topology]
      SCH[Cluster Scheduler]
      ATL[Atlas]
    end

    subgraph Cognitive["v3 Cognitive"]
      MEM[Operational Memory]
      KNOW[Causal Knowledge]
      CONS[Consensus]
      RESAI[Research AI]
    end

    subgraph Intelligence["v2 Intelligence"]
      GRAPH[Resource Graph]
      REASON[Reasoning]
      TWIN[Host Digital Twin]
      CTX[Context]
      RINT[Research Intel]
    end

    subgraph Operating["v1 Operating"]
      TEL[Telemetry]
      POL[Policy Engine]
      SAF[Safety]
      DEC[Decision]
      OBS[Observatory]
      EXP[Explainability]
    end

    Surfaces --> Horizon
    Surfaces --> Nexus
    HOR --> HOBS
    HOBS --> CLOUD
    HOBS --> ITWIN
    HOBS --> GKG
    HOBS --> PLAN
    CLOUD --> ITWIN
    PLAN --> ITWIN
    Horizon --> Distributed
    Nexus --> Intelligence
    Distributed --> Cognitive
    Cognitive --> Intelligence
    Intelligence --> Operating
```

## Safety boundary

```mermaid
flowchart LR
    Tel[Telemetry] --> Rec[Recommendation]
    Rec --> Human{Human approval}
    Human -->|outside AetherOS| Ops[Operator tools]
    Rec -.->|forbidden edge| Mut[OS / Cloud / K8s mutation]
    style Mut fill:#222,stroke:#c44,color:#fff
```

## Related docs

- [architecture.md](../architecture.md) — narrative overview
- [pipeline.md](pipeline.md) — intelligence pipeline
- [generations.md](generations.md) — generation map
- [extensibility.md](extensibility.md) — plugins · API · enterprise
- [cloud_federation.md](../cloud_federation.md)
- [infrastructure_twin.md](../infrastructure_twin.md)
- [global_knowledge_graph.md](../global_knowledge_graph.md)
- [planetary_scheduler.md](../planetary_scheduler.md)
- [horizon_observatory.md](../horizon_observatory.md)
