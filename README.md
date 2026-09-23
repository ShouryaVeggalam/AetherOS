# AetherOS v1.1 — Observatory

Real-time intelligence center panel with SQLite temporal memory.

## Observatory

| Module | Role |
|--------|------|
| `models.py` | `TelemetryPoint`, `SystemEvent`, `TimelineWindow` |
| `recorder.py` | `HistoryRecorder` → `data/observatory.db` + 300-sample RAM window |
| `events.py` | Spike / pressure / intent / research / safety + observations |
| `timeline.py` | Scrolling event log |
| `renderer.py` | CPU/Memory/Disk sparklines + focus graph + AI observations |

## Keys

| Key | Action |
|-----|--------|
| **O** | Toggle Observatory |
| **←** | Scroll history |
| **T** | Cycle CPU → Memory → Disk |
| **ESC** | Leave Observatory |

```bash
cd /Users/shouryaveggalam/AetherOS
source .venv/bin/activate
python -m aetheros
```

Read-only. No OS commands. No Textual — Rich only.
