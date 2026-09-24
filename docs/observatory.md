# Observatory

The Observatory gives AetherOS **temporal memory**. Instead of showing only the current sample, it stores telemetry history and surfaces trends, spikes, and derived observations.

## Responsibilities

| Module | Role |
|--------|------|
| `models.py` | `TelemetryPoint`, `SystemEvent`, `TimelineWindow` |
| `recorder.py` | Append-only SQLite + 300-sample ring buffer |
| `events.py` | Spike / pressure / intent / research / safety events |
| `timeline.py` | Scrollable event log |
| `renderer.py` | Sparklines, focus graph, observation list |

## Persistence

Database path (default): `data/observatory.db`

Tables:

- `telemetry_history` — timestamp, cpu, memory, disk, battery, intent
- `events` — timestamp, type, severity, title, description

History is **never overwritten**. The in-memory window caps at 300 samples for UI performance.

## Event conditions (examples)

- **CPU Spike** — CPU rises more than 20% within ~5 seconds
- **Memory Pressure** — memory exceeds 85%
- **Intent Changed** — operator switches profile
- **Research Completed** — research run finishes
- **Safety Blocked** — recommendation rejected

## Observations

AI observation lines are derived only from recorded history (for example, recovery after memory pressure). The Observatory does not invent narrative.

## Dashboard

| Key | Action |
|-----|--------|
| `O` | Toggle Observatory |
| `T` | Cycle CPU / Memory / Disk focus graph |
| `←` / `→` | Scroll history / timeline |
| `ESC` | Leave overlay |

## Safety

Observatory is read-only. It does not execute OS commands or change kernel state.
