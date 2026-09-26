# Cloud Federation Engine — AetherOS v6.0 P1

**Package:** [`aetheros/cloud/`](../aetheros/cloud/)  
**Dashboard:** **C** → Cloud Federation (**;** remains Cluster overview)  
**Status:** Read-only infrastructure federation

---

## Philosophy

AetherOS federates **observations** of cloud and edge inventory. It never
provisions, deletes, restarts, or modifies cloud resources.

- No Terraform execution
- No kubectl execution
- No cloud SDK mutations
- No credential storage

```mermaid
flowchart LR
    AWS[AWS inventory] --> Norm[Normalize]
    AZ[Azure inventory] --> Norm
    GCP[GCP inventory] --> Norm
    K8S[Kubernetes inventory] --> Norm
    DOCK[Docker inventory] --> Norm
    EDGE[Edge inventory] --> Norm
    Norm --> Reg[CloudRegistry]
    Reg --> Snap[Immutable Snapshot]
    Snap --> UI[Rich Dashboard / JSON export]
    Note1[Humans approve any change outside AetherOS]
```

---

## Provider architecture

Every provider is a **Federation Node** implemented as a read-only adapter:

| Adapter | Resource types |
|---------|----------------|
| `AWSProvider` | EC2 · EBS · VPC · RDS |
| `AzureProvider` | VM · Storage · Network |
| `GCPProvider` | Compute · Disk · Network |
| `KubernetesProvider` | Cluster · Node · Pod · Service |
| `DockerProvider` | Container · Image |
| `EdgeProvider` | Device · Gateway |

Adapters accept optional inventory mappings (fixtures or external exports).
When no inventory is supplied, a static **demo** inventory seeds the dashboard.

```mermaid
sequenceDiagram
    participant Op as Operator
    participant Eng as CloudFederationEngine
    participant Ad as Provider Adapter
    participant Reg as CloudRegistry
    participant Snap as Snapshot Engine

    Op->>Eng: capture_all (read-only)
    Eng->>Ad: observe(inventory?)
    Ad-->>Eng: CloudResource[]
    Eng->>Reg: register(provider, resources)
    Eng->>Snap: capture(providers, resources)
    Snap-->>Eng: InfrastructureSnapshot (frozen)
    Note over Eng,Snap: JSON serialize only · never pickle · never mutate cloud
```

---

## Normalized resource model

All providers map into one frozen dataclass:

```text
CloudResource
  id · provider · type · name · region · metadata
```

Providers themselves are:

```text
CloudProvider
  id · name · version · region · connected
```

Snapshots:

```text
InfrastructureSnapshot
  timestamp · providers · resources · topology_hash
```

Health:

```text
FederationHealth
  online · degraded · offline · confidence
```

---

## Snapshot lifecycle

1. **capture()** — freeze providers + resources; compute `topology_hash`
2. **serialize()** — canonical or pretty JSON (no pickle)
3. **compare()** — membership + hash diff (`SnapshotDiff`)
4. **hash()** — recompute SHA-256 topology digest for verification

Registry tracks connected providers, regions, API version, snapshot age, and
health. Credentials remain external and are never stored.

---

## Dashboard

Press **C** for Cloud Federation. Views (cycle with **]**):

- Providers
- Regions
- Resources
- Health
- Snapshots

Status line always shows **Read Only**.

---

## Safety invariants

1. Observation before action (AetherOS never acts on cloud APIs).
2. Explainable census (normalized model + topology hash).
3. Simulation / comparison only — no apply path.
4. Humans remain in control of any real-world change.
