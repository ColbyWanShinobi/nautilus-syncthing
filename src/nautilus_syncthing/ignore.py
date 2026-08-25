"""Conservative .stignore matching for marking excluded paths in Nautilus."""
from __future__ import annotations

from fnmatch import fnmatchcase
from pathlib import Path


def is_ignored(folder: Path, path: Path) -> bool:
    """Handle ordinary .stignore patterns locally; Syncthing remains authoritative."""
    ignore = folder / ".stignore"
    try:
        patterns = ignore.read_text(encoding="utf-8", errors="replace").splitlines()
        relative = path.relative_to(folder).as_posix()
    except (OSError, ValueError):
        return False
    for pattern in patterns:
        pattern = pattern.strip()
        if not pattern or pattern.startswith(("#", "!", "(?")):
            continue
        pattern = pattern.lstrip("/")
        if fnmatchcase(relative, pattern) or fnmatchcase(path.name, pattern):
            return True
    return False
