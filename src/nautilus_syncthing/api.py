"""Small, timeout-bound Syncthing REST client; no shell commands involved."""
from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import Settings


class ApiError(RuntimeError):
    pass


class SyncthingApi:
    def __init__(self, settings: Settings, timeout: float = 2.0):
        self.settings, self.timeout = settings, timeout

    def get(self, path: str, **query: str) -> Any:
        suffix = f"?{urlencode(query)}" if query else ""
        request = Request(f"{self.settings.url}/rest/{path.lstrip('/')}{suffix}", headers={"X-API-Key": self.settings.api_key})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ApiError(str(exc)) from exc

    def system_status(self) -> dict[str, Any]:
        return self.get("system/status")

    def connections(self) -> dict[str, Any]:
        return self.get("system/connections")

    def config(self) -> dict[str, Any]:
        return self.get("config")

    def folder_status(self, folder: str) -> dict[str, Any]:
        return self.get("db/status", folder=folder)

    def folder_errors(self, folder: str) -> dict[str, Any]:
        return self.get("folder/errors", folder=folder)

    def events(self, since: int, timeout: int = 30) -> list[dict[str, Any]]:
        return self.get("events", since=str(since), timeout=str(timeout))
