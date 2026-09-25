# Plugin trust model

AetherOS plugins are **load-time gated**, not OS-isolated. The SDK sandbox
is an AST + source scan before ``import``. It is **not** a container, seccomp
profile, or capability drop.

## Trust boundary

| Claim | Reality |
|-------|---------|
| Forbidden APIs blocked at load | Yes — `PluginSandbox.validate_path` |
| Runtime isolation after import | **No** — verified plugins run in-process |
| Network / disk / eval fully impossible | **No** — deny-list is best-effort |
| Humans still approve OS actions | Yes — plugins contribute advice/telemetry only |

Treat third-party plugins as **semi-trusted code**. Prefer bundled plugins
under `aetheros/plugins/` or review source before enabling.

## Deny-list (load-time)

Rejected module roots / prefixes include: `subprocess`, `ctypes`, `socket`,
`pty`, `fcntl`, `multiprocessing`, `signal`, `http`, `urllib`, `requests`,
`httpx`, `pickle`, `importlib`, `shutil`, `code`, `codeop`.

Rejected calls / patterns include: `os.system`, `eval` / `exec` / `compile` /
`__import__`, dangerous `os.*` process/fs attrs, and the text tokens
`sudo`, `os.system`, `subprocess.`, `ctypes.`.

## Safe contribution surface

Plugins should only use `aetheros.sdk` facades:

- `PluginAPI.telemetry` — contribute samples
- `PluginAPI.dashboard` — widgets (display)
- `PluginAPI.history` / `simulation` — read-only helpers

Never shell out. Never request sudo. Never mutate host state.

## Related

- `aetheros/sdk/sandbox.py`
- [CELESTRA charter](CELESTRA.md) feature gate
- [Architecture](architecture.md)
