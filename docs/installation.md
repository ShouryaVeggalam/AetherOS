# Installation — AetherOS

Install and run AetherOS on a developer workstation or CI agent.

**Requirements:** Python **3.12+** · Linux (Ubuntu recommended), **WSL2**, or **macOS**  
**Privileges:** None required for core paths (userspace `psutil` only)

---

## 1. Clone

```bash
git clone https://github.com/ShouryaVeggalam/AetherOS.git
cd AetherOS
```

Use the `main` branch for stable releases, or a feature branch (e.g. Horizon work) when reviewing PRs.

---

## 2. Virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Linux / macOS / WSL2
# .venv\Scripts\activate           # Windows (experimental)
python -m pip install -U pip
```

---

## 3. Install (editable + dev tools)

```bash
pip install -e ".[dev]"
```

This installs:

- The `aetheros` package and console entry points
- Test / lint tooling (`pytest`, `ruff`, `black`, coverage)

Optional build tooling for packaging:

```bash
pip install build twine
```

---

## 4. Verify

```bash
python -c "import aetheros; print(aetheros.__version__)"
python -m compileall -q aetheros
ruff check .
black --check .
pytest --cov=aetheros --cov-fail-under=90
```

---

## 5. Run operator surfaces

| Command | Surface |
|---------|---------|
| `python -m aetheros` or `aetheros` | Rich operator dashboard |
| `aetheros-horizon` | Horizon Observatory (global infrastructure views) |
| `aetheros-atlas` | Atlas presentation observatory |
| `uvicorn aetheros.api.app:app --reload` | Read-only FastAPI (`/docs` OpenAPI) |

```bash
# Dashboard
aetheros

# Horizon Observatory (O/C/T/K/W/D/G/R/H · Q quit)
aetheros-horizon --page overview

# API
uvicorn aetheros.api.app:app --host 127.0.0.1 --port 8000
```

### Python SDK sketch

```python
from aetheros import AetherClient

client = AetherClient(base_url="http://127.0.0.1:8000")
print(client.health())
```

---

## 6. Benchmarks (optional)

```bash
python scripts/run_benchmarks.py
# → Markdown table + reports/benchmarks.json
```

Methodology: [docs/benchmarks.md](benchmarks.md)

---

## Platform notes

### Ubuntu / Debian

```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3-pip
```

### WSL2

Use an Ubuntu WSL distro, install Python 3.12 as above, and run inside a real terminal (Windows Terminal recommended). TTY-less SSH sessions may blank the Rich UI.

### macOS

```bash
brew install python@3.12
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

If `psutil` raises `PermissionError`, grant **Full Disk Access** to your terminal app.

### Docker (read-only exploration)

AetherOS itself does not ship a required container image for core use. If you containerize for demos, mount a TTY (`docker run -it`) and do **not** grant the process host mutation capabilities.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `python: command not found` | Invoke `python3.12` explicitly |
| Blank / broken TUI | Run in an interactive TTY (not raw CI logs) |
| Import errors after `git pull` | Re-run `pip install -e ".[dev]"` |
| Coverage / CI red | `pytest --cov=aetheros --cov-fail-under=90` |
| No battery metrics | Expected on many desktops / VMs / CI |
| Horizon / Atlas keys do nothing | Confirm you launched `aetheros-horizon` / `aetheros-atlas`, not only the main dashboard |

---

## What AetherOS will never do on install

- Install kernel modules or drivers
- Open privileged ports by default
- Run Terraform / kubectl apply / cloud provisioners
- Exfiltrate telemetry (collection is local unless *you* point the API elsewhere)

---

## Next steps

- [Architecture](architecture.md)
- [Horizon Observatory](horizon_observatory.md)
- [Contributing](../CONTRIBUTING.md)
- [v6.0 Horizon release notes](releases/v6.0.0.md)
