# Screenshots & demo assets

Terminal recordings and **placeholders** for the public README and launch pages.

## Expected files

| File | Subject | Status |
|------|---------|--------|
| `demo.gif` | **Primary hero loop** (8–12s) | Placeholder shipped |
| `dashboard.gif` | Main operator dashboard | Placeholder shipped |
| `horizon.gif` | Horizon Observatory (`aetheros-horizon`) | Placeholder shipped |
| `cloud.gif` | Cloud Federation panel | Placeholder shipped |
| `planetary.gif` | Planetary / Worldwide Scheduler | Placeholder shipped |
| `observatory.gif` | Observatory graphs + timeline | Placeholder shipped |
| `cluster.gif` | Cluster overview | Placeholder shipped |
| `predictive.gif` | Predictive horizons | Placeholder shipped |

Placeholders are dark-terminal labeled loops so GitHub never shows broken images.
**Replace them with real captures before marketing screenshots.**

## Capture guidelines

1. Dark terminal, readable font (14–16pt).
2. Window ≈ **120×40** characters.
3. Prefer **5–12 second** loops; keep files modest (&lt; 5 MB each when possible).
4. Tools: [`asciinema`](https://asciinema.org/) + [`agg`](https://github.com/asciinema/agg), [`vhs`](https://github.com/charmbracelet/vhs), or OS screen recording → GIF.
5. Do **not** commit secrets, personal credential paths, or raw uncompressed video.

### Suggested recording script (Horizon)

```bash
# Terminal A
aetheros-horizon --page overview
# Press: O → C → K → W → D → H → Q
```

### Suggested recording script (Dashboard)

```bash
aetheros
# Press: ? · C · I · K · W · ESC · Q
```

## README embedding

```markdown
![Demo](docs/screenshots/demo.gif)
![Dashboard](docs/screenshots/dashboard.gif)
![Horizon](docs/screenshots/horizon.gif)
![Cloud](docs/screenshots/cloud.gif)
![Planetary](docs/screenshots/planetary.gif)
![Observatory](docs/screenshots/observatory.gif)
![Cluster](docs/screenshots/cluster.gif)
![Predictive](docs/screenshots/predictive.gif)
```

## Maintainer checklist

- [ ] Replace `demo.gif` with live hero capture
- [ ] Replace `dashboard.gif`
- [ ] Replace `horizon.gif` / `cloud.gif` / `planetary.gif`
- [ ] Replace `observatory.gif` / `cluster.gif` / `predictive.gif`
- [ ] Visually QA on GitHub mobile and desktop
- [ ] Confirm no PII / secrets in frames
