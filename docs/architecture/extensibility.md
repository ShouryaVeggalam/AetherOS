# Architecture diagram — Extensibility & enterprise

How plugins, marketplace, public API, and enterprise controls relate in **v5.0.0 Nexus**.

```mermaid
flowchart LR
    subgraph Authors
      MAN[plugin.yaml]
      CODE[Plugin module]
    end

    subgraph SDK["plugins/sdk"]
      LOAD[Loader]
      SAND[Sandbox]
      CAP[Capabilities]
      EVT[Events]
    end

    subgraph Market["aetheros.marketplace"]
      CAT[Catalog]
      INST[Install / Verify]
      EN[Enable]
    end

    subgraph API["aetheros.api"]
      V1["/api/v1/*"]
      KEYS[API key auth]
    end

    subgraph Ent["aetheros.enterprise"]
      ORG[Orgs / Workspaces]
      RBAC[RBAC]
      AUD[Audit / Compliance]
    end

    MAN --> LOAD
    CODE --> LOAD
    LOAD --> SAND --> CAP --> EVT
    CAT --> INST --> EN --> LOAD
    ORG --> RBAC --> KEYS --> V1
    V1 --> AUD
    EN --> V1
```

## Trust model

1. Manifests declare capabilities; the sandbox deny-list blocks dangerous imports.
2. Marketplace verify/enable is advisory and local — no remote code execution by default.
3. Enterprise audit logs are append-oriented; they do not grant shell or sudo.
4. Untrusted plugins must not be enabled in production.

See [plugin_sdk.md](../plugin_sdk.md), [marketplace.md](../marketplace.md), [enterprise.md](../enterprise.md).
