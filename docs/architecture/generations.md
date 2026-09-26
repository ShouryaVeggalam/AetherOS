# Architecture diagram — Generations

Historical generation labels used across AetherOS documentation, aligned to the
**v5.0.0 Nexus** production release.

```mermaid
flowchart LR
    V1["v1 Operating<br/>telemetry · policy · safety"]
    V2["v2 Intelligence<br/>graph · reason · twin"]
    V3["v3 Cognitive<br/>memory · causal · consensus"]
    V4["v4 Distributed<br/>federation · topology · atlas"]
    V5["v5 Nexus<br/>plugins · API · enterprise"]
    HZ["Horizon+<br/>planetary overlays"]

    V1 --> V2 --> V3 --> V4 --> V5 --> HZ
```

```mermaid
mindmap
  root((AetherOS Nexus))
    Observe
      Telemetry
      Observatory
      Memory
    Reason
      Resource Graph
      Causal KG
      Cognition
    Simulate
      Digital Twin
      Scheduler
      Research Lab
    Explain
      Evidence
      Policy Studio
      Safety
    Extend
      Plugin SDK
      Marketplace
      Enterprise
```

Legacy generation names (Horizon / Genesis / Sentinel / Fabric / Infinity) remain
as packages and dashboard surfaces; they are not superseded by Nexus packaging.
