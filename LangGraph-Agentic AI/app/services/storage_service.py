from __future__ import annotations

from pathlib import Path


class StorageService:
    """Simple local filesystem storage helper."""

    def ensure_dirs(self, *paths: str) -> None:
        for path in paths:
            Path(path).mkdir(parents=True, exist_ok=True)
