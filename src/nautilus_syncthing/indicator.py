"""Independent AppIndicator/KStatusNotifier-compatible Syncthing status app."""
from __future__ import annotations

from pathlib import Path
import webbrowser

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # type: ignore

from .config import discover
from .state import StateService


class Indicator:
    def __init__(self) -> None:
        try:
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3 as AppIndicator3  # type: ignore
        except (ImportError, ValueError):
            gi.require_version("AppIndicator3", "0.1")
            from gi.repository import AppIndicator3  # type: ignore
        self._appindicator = AppIndicator3
        self.state = StateService()
        self.state.start()
        self.indicator = AppIndicator3.Indicator.new("nautilus-syncthing", "folder-sync-symbolic", AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.menu = Gtk.Menu()
        self.status_item = Gtk.MenuItem(label="Connecting to Syncthing…")
        self.status_item.set_sensitive(False); self.menu.append(self.status_item)
        self._add("Open Syncthing", self.open_ui)
        self._add("View status and errors", self.open_ui)
        self._add("Open synced folders", self.open_folders)
        self._add("Quit", Gtk.main_quit)
        self.menu.show_all(); self.indicator.set_menu(self.menu)
        GLib.timeout_add_seconds(5, self.refresh)
        self.refresh()

    def _add(self, label, callback) -> None:
        item = Gtk.MenuItem(label=label); item.connect("activate", lambda *_: callback()); self.menu.append(item)

    def refresh(self) -> bool:
        snap = self.state.summary()
        if not snap.online:
            text, icon = "Syncthing offline", "network-offline-symbolic"
        elif snap.errors:
            text, icon = f"Syncthing: {len(snap.errors)} error(s)", "dialog-error-symbolic"
        elif snap.transfers or any(state == "syncing" for _, state in snap.folders.values()):
            text, icon = "Syncthing is syncing", "folder-sync-symbolic"
        else:
            text, icon = "Syncthing up to date", "emblem-ok-symbolic"
        self.status_item.set_label(text); self.indicator.set_icon_full(icon, text)
        return True

    @staticmethod
    def open_ui() -> None:
        settings = discover()
        if settings: webbrowser.open(settings.url)

    def open_folders(self) -> None:
        for root in self.state.summary().folders:
            # argv form avoids shell injection and works with spaces/non-ASCII paths.
            import subprocess
            subprocess.Popen(["xdg-open", str(root)], start_new_session=True)


def main() -> None:
    Indicator()
    Gtk.main()
