"""AetherOS entrypoint for documented quick start (`python main.py`).

Delegates to the Rich operator dashboard. Recommendation-only userspace UI.
"""

from __future__ import annotations

from aetheros.dashboard.app import main

if __name__ == "__main__":
    main()
