"""Nautilus 4.x Python extension; it never performs I/O from provider calls."""
from __future__ import annotations

from pathlib import Path
import subprocess
import webbrowser

import gi
gi.require_version("Nautilus", "4.0")
from gi.repository import GObject, Nautilus  # type: ignore

from .config import discover
from .state import StateService

_EMBLEMS = {
    "synced": "nautilus-syncthing-synced", "syncing": "nautilus-syncthing-syncing",
    "error": "nautilus-syncthing-error", "offline": "nautilus-syncthing-offline",
    "ignored": "nautilus-syncthing-ignored",
}


class SyncthingExtension(GObject.GObject, Nautilus.InfoProvider, Nautilus.MenuProvider):
    """Current API 4 provider. FileInfo is neither retained nor queried over HTTP."""
    def __init__(self):
        super().__init__()
        self.state = StateService()
        self.state.start()

    @staticmethod
    def _path(file: Nautilus.FileInfo) -> Path | None:
        location = file.get_location()
        if not location or not location.is_native(): return None
        raw = location.get_path()
        return Path(raw) if raw else None

    def update_file_info(self, file: Nautilus.FileInfo) -> Nautilus.OperationResult:
        path = self._path(file)
        if path:
            status = self.state.request(path)
            emblem = _EMBLEMS.get(status)
            if emblem: file.add_emblem(emblem)
        return Nautilus.OperationResult.COMPLETE

    def get_file_items(self, files: list[Nautilus.FileInfo]):
        paths = [self._path(file) for file in files]
        paths = [path for path in paths if path]
        if not paths: return []
        item = Nautilus.MenuItem(name="SyncthingExtension::status", label="Syncthing status", tip="Open Syncthing's web interface")
        item.connect("activate", self._open_ui)
        return [item]

    def get_background_items(self, folder: Nautilus.FileInfo):
        path = self._path(folder)
        if not path: return []
        item = Nautilus.MenuItem(name="SyncthingExtension::open-folder", label="Open in Syncthing", tip="Open this folder in Syncthing's web interface")
        item.connect("activate", self._open_ui)
        return [item]

    @staticmethod
    def _open_ui(_item: Nautilus.MenuItem) -> None:
        settings = discover()
        if settings: webbrowser.open(settings.url)


# Nautilus loads this file from its extension directory. The installed wrapper
# imports this class, keeping application modules importable and testable.
