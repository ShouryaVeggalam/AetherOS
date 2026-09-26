# Screenshots & demo assets

This directory holds terminal recordings for the public README.

## Expected files

| File | Subject |
|------|---------|
| `demo.gif` | **Primary demo loop** — Nexus dashboard (8–12s) |
| `dashboard.gif` | Main operator dashboard (telemetry + decision + safety) |
| `observatory.gif` | Observatory graphs, timeline, observations |
| `cluster.gif` | Cluster overview with multiple nodes |
| `predictive.gif` | Predictive horizons, trends, risk |

## Capture guidelines

1. Use a dark terminal with a readable font (e.g. 14–16pt).
2. Window size ≈ **120×40** characters for consistent framing.
3. Prefer **5–12 second** loops; keep file size modest.
4. Tools: `asciinema` + `agg`, or `vhs`, or macOS screen recording → GIF.
5. Do **not** commit secrets, personal paths with credentials, or oversized raw videos.

## README embedding

The root README references:

```markdown
![Operator Dashboard](docs/screenshots/dashboard.gif)
![Observatory](docs/screenshots/observatory.gif)
![Cluster Overview](docs/screenshots/cluster.gif)
![Predictive Intelligence](docs/screenshots/predictive.gif)
![Demo (placeholder)](docs/screenshots/demo.gif)
```

Until GIFs are recorded, GitHub will show broken-image placeholders. That is expected for documentation-first packaging of **v5.0.0 Nexus**.

## Checklist for maintainers

- [ ] Record `demo.gif` (primary README hero demo)
- [ ] Record `dashboard.gif`
- [ ] Record `observatory.gif`
- [ ] Record `cluster.gif`
- [ ] Record `predictive.gif`
- [ ] Visually QA on GitHub mobile and desktop
