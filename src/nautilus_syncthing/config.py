"""Configuration and deliberately local Syncthing API discovery."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import stat
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class Settings:
    url: str
    api_key: str


def _private(path: Path) -> bool:
    """Do not read credentials from a file writable/readable by other users."""
    try:
        return stat.S_IMODE(path.stat().st_mode) & 0o077 == 0
    except OSError:
        return False


def _url(address: str) -> str:
    address = address.strip()
    if address.startswith(("http://", "https://")):
        return address.rstrip("/")
    # Syncthing's default GUI address is usually 127.0.0.1:8384.
    host = address
    if host.startswith("["):
        host = host.replace("[", "", 1).replace("]", "", 1)
    return f"http://{host}".rstrip("/")


def discover() -> Settings | None:
    """Read a local daemon's GUI address/key, or explicit environment overrides.

    SYNCTHING_API_URL and SYNCTHING_API_KEY are intended for containers and
    unusual daemon profiles. No credentials are embedded in code or logs.
    """
    url, key = os.environ.get("SYNCTHING_API_URL"), os.environ.get("SYNCTHING_API_KEY")
    if url and key:
        return Settings(_url(url), key)
    # Syncthing 1.27 moved the Unix default from XDG_CONFIG_HOME to
    # XDG_STATE_HOME. Retain the old path as a migration fallback.
    explicit = os.environ.get("SYNCTHING_CONFIG")
    candidates = [Path(explicit)] if explicit else [
        Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "syncthing" / "config.xml",
        Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "syncthing" / "config.xml",
    ]
    for config in candidates:
        if not _private(config):
            continue
        try:
            gui = ET.parse(config).getroot().find("gui")
            if gui is None:
                continue
            address = gui.findtext("address")
            api_key = gui.findtext("apikey")
            if address and api_key:
                return Settings(_url(address), api_key)
        except (OSError, ET.ParseError):
            continue
    return None
