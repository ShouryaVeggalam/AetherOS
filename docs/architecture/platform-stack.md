# Architecture diagram — Platform stack (Nexus)

Layered view of **AetherOS v5.0.0 Nexus** packages as consumed by operators and integrations.

```mermaid
flowchart TB
    subgraph Surfaces["Operator surfaces"]
      DASH[Rich Dashboard]
      ATLAS[Atlas]
      WEBAPI["FastAPI /api/v1"]
      PYSDK[AetherClient]
    end

    subgraph Nexus["v5 Nexus layer"]
      PLG[Plugin SDK]
      MKT[Marketplace]
      PST[Policy Studio]
      ENT[Enterprise]
    end

    subgraph Distributed["v4 Distributed"]
      FED[Federation]
      TOP[Topology]
      SCH[Scheduler]
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
      TWIN[Digital Twin]
      CTX[Context]
      RINT[Research Intel]
    end

    subgraph Foundations["v1 Foundations"]
      TEL[Telemetry]
      PE[Policy Engine]
      SAF[Safety]
      DEC[Decision]
      OBS[Observatory]
      EXP[Explainability]
    end

    DASH --> Foundations
    ATLAS --> Distributed
    WEBAPI --> Nexus
    PYSDK --> WEBAPI
    Nexus --> Cognitive
    Distributed --> Intelligence
    Cognitive --> Intelligence
    Intelligence --> Foundations
```

## Notes

- Surfaces never bypass Safety / HITL for host mutation (AetherOS has no mutation path).
- Enterprise middleware authenticates API access; it does not expand privileges on the host OS.
