# Atlas (v4.0 P5 + v5 facade)

**Atlas Dashboard** is the Rich terminal observatory for distributed
infrastructure (presentation only).

```bash
aetheros-atlas
python -m aetheros.atlas --page overview
```

Hotkeys: **O** Overview · **F** Federation · **T** Topology · **S** Scheduler ·
**G** Consensus · **D** Twin · **R** Research · **H** Health · **Q** Quit

Docs: [atlas_dashboard.md](../../docs/atlas_dashboard.md)

## Compatibility facade

Atlas still re-exports Horizon world graph + Global Twin under the historical
generation name:

```python
from aetheros.atlas import WorldGraph, HorizonRuntime, GlobalTwin
```

## Invariants

- Read-only / simulation-only presentation
- Rich only (no Textual)
- No remote execution
- No telemetry / twin / schema mutations
