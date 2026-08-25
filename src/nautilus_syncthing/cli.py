"""A non-GUI status command useful for diagnostics and support."""
from __future__ import annotations
import json
from .api import SyncthingApi
from .config import discover

def main() -> None:
    settings = discover()
    if not settings:
        raise SystemExit("Syncthing credentials unavailable (check config.xml permissions or environment)")
    print(json.dumps(SyncthingApi(settings).system_status(), indent=2, sort_keys=True))
