# Architecture diagram — Intelligence pipeline

Mermaid source for the AetherOS **Observe → Reason → Simulate → Explain** loop
shipped with **v5.0.0 Nexus**.

```mermaid
flowchart TD
    subgraph Observe
      TEL[TelemetryCollector]
      OBS[Observatory / Memory]
    end

    subgraph Reason
      GR[Resource Graph]
      CKG[Causal Knowledge]
      REA[Graph Reasoning]
      COG[Cognition Core]
    end

    subgraph Simulate
      TWIN[Digital Twin]
      SCH[Scheduler What-if]
      LAB[Research Lab]
    end

    subgraph Explain
      EXP[Explainability]
      POL[Policy Studio]
      SAF[Safety Gate]
      DEC[Decision Engine]
    end

    TEL --> OBS --> GR --> REA --> TWIN
    GR --> CKG --> COG
    TWIN --> EXP
    COG --> EXP
    SCH --> EXP
    LAB --> EXP
    EXP --> POL --> SAF --> DEC
    DEC --> HITL[Human Approval]
    HITL -.->|no mutation by AetherOS| TEL
```

## Invariants

- All edges are **read-only** with respect to the host OS.
- Simulation never writes kernel or process state.
- Recommendations require human approval outside AetherOS.
