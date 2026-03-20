"""File watch event source — monitors files for changes via polling."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable

from mu_dsu.events.types import Event, NORMAL


class FileWatchSource:
    """Monitors files for changes by polling mtime. No external dependencies."""

    def __init__(
        self,
        paths: list[str | Path],
        poll_interval: float = 1.0,
        event_type: str = "file.changed",
    ) -> None:
        self._paths = [Path(p) for p in paths]
        self._poll_interval = poll_interval
        self._event_type = event_type
        self._running = False
        self._mtimes: dict[Path, float] = {}

    @property
    def name(self) -> str:
        return "file_watch"

    async def start(self, emit: Callable[[Event], None]) -> None:
        self._running = True
        # Record initial mtimes
        for p in self._paths:
            if p.exists():
                self._mtimes[p] = p.stat().st_mtime

        while self._running:
            await asyncio.sleep(self._poll_interval)
            if not self._running:
                break
            for p in self._paths:
                if not p.exists():
                    continue
                current_mtime = p.stat().st_mtime
                old_mtime = self._mtimes.get(p)
                if old_mtime is not None and current_mtime != old_mtime:
                    self._mtimes[p] = current_mtime
                    emit(Event(
                        type=self._event_type,
                        source=self.name,
                        payload={"path": str(p), "old_mtime": old_mtime, "new_mtime": current_mtime},
                        priority=NORMAL,
                    ))
                elif old_mtime is None:
                    self._mtimes[p] = current_mtime

    async def stop(self) -> None:
        self._running = False
