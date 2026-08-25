"""Bounded asynchronous state cache shared by the extension and indicator."""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
import queue
import threading
import time
from typing import Literal

from .api import ApiError, SyncthingApi
from .config import discover
from .ignore import is_ignored

State = Literal["synced", "syncing", "error", "offline", "ignored", "unknown"]

@dataclass
class Snapshot:
    online: bool = False
    folders: dict[Path, tuple[str, State]] = field(default_factory=dict)
    transfers: set[tuple[str, str]] = field(default_factory=set)
    errors: list[str] = field(default_factory=list)
    updated: float = 0.0


class StateService:
    """One worker, event long-polling, and a hard cap on scheduled file probes."""
    def __init__(self, cache_limit: int = 512):
        self.cache_limit = cache_limit
        self.snapshot = Snapshot()
        self._wanted: OrderedDict[Path, None] = OrderedDict()
        self._lock = threading.RLock()
        self._wake: queue.Queue[None] = queue.Queue(maxsize=1)
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, name="syncthing-state", daemon=True)
            self._thread.start()

    def request(self, path: Path) -> State:
        """Return immediately. The worker refreshes state after this call."""
        with self._lock:
            result = self._state_for(path)
            self._wanted[path] = None
            self._wanted.move_to_end(path)
            while len(self._wanted) > self.cache_limit:
                self._wanted.popitem(last=False)
        try: self._wake.put_nowait(None)
        except queue.Full: pass
        return result

    def _state_for(self, path: Path) -> State:
        if not self.snapshot.online:
            return "offline" if self.snapshot.updated else "unknown"
        for root, (folder_id, folder_state) in self.snapshot.folders.items():
            try: path.relative_to(root)
            except ValueError: continue
            if is_ignored(root, path): return "ignored"
            if (folder_id, path.relative_to(root).as_posix()) in self.snapshot.transfers: return "syncing"
            return folder_state
        return "unknown"

    def summary(self) -> Snapshot:
        with self._lock:
            return Snapshot(self.snapshot.online, dict(self.snapshot.folders), set(self.snapshot.transfers), list(self.snapshot.errors), self.snapshot.updated)

    def _run(self) -> None:
        since = 0
        folders: dict[Path, tuple[str, State]] = {}
        transfers: set[tuple[str, str]] = set()
        errors: list[str] = []
        refresh_at = 0.0
        while not self._stop.is_set():
            settings = discover()
            if not settings:
                self._publish(False, {}, set(), ["Syncthing API credentials were not found"])
                self._stop.wait(30); continue
            try:
                api = SyncthingApi(settings)
                # Refresh aggregate REST status at most every 30 seconds.
                if time.monotonic() >= refresh_at:
                    config = api.config()
                    folders, errors = {}, []
                    for folder in config.get("folders", []):
                        root, ident = Path(folder["path"]), folder["id"]
                        status = api.folder_status(ident)
                        reported_errors = api.folder_errors(ident).get("errors", [])
                        state: State = "error" if reported_errors else ("syncing" if status.get("needBytes", 0) else "synced")
                        folders[root] = (ident, state)
                        errors.extend(str(error.get("error", error)) if isinstance(error, dict) else str(error) for error in reported_errors)
                    refresh_at = time.monotonic() + 30
                # This is a long poll, not a tight status poll.
                events = api.events(since, timeout=30)
                if events: since = max(int(e.get("id", 0)) for e in events)
                transfers = self._apply_events(transfers, events)
                self._publish(True, folders, transfers, errors)
            except ApiError:
                self._publish(False, {}, set(), ["Cannot reach Syncthing"])
                self._stop.wait(15)

    @staticmethod
    def _apply_events(active: set[tuple[str, str]], events: list[dict]) -> set[tuple[str, str]]:
        active = set(active)
        for event in events:
            data = event.get("data", {})
            folder, item = data.get("folder"), data.get("item")
            if not folder or not item: continue
            key = (folder, item)
            if event.get("type") == "ItemStarted": active.add(key)
            elif event.get("type") in {"ItemFinished", "ItemFailed"}: active.discard(key)
        return active

    def _publish(self, online: bool, folders: dict, transfers: set, errors: list[str]) -> None:
        with self._lock:
            self.snapshot = Snapshot(online, folders, transfers, errors[:20], time.monotonic())
