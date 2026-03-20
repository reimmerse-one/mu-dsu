"""Tests for FileWatchSource."""

import asyncio
import tempfile
from pathlib import Path

from mu_dsu.events.sources.file_watch import FileWatchSource
from mu_dsu.events.types import Event


class TestFileWatchSource:
    def test_detects_file_change(self, tmp_path):
        f = tmp_path / "config.txt"
        f.write_text("v1")
        events: list[Event] = []
        source = FileWatchSource(paths=[f], poll_interval=0.02)

        async def run():
            task = asyncio.create_task(source.start(events.append))
            await asyncio.sleep(0.05)  # Let it record initial mtime
            f.write_text("v2")  # Modify
            await asyncio.sleep(0.1)  # Wait for detection
            await source.stop()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(run())
        assert len(events) >= 1
        assert events[0].type == "file.changed"
        assert events[0].payload["path"] == str(f)

    def test_no_event_when_unchanged(self, tmp_path):
        f = tmp_path / "stable.txt"
        f.write_text("same")
        events: list[Event] = []
        source = FileWatchSource(paths=[f], poll_interval=0.02)

        async def run():
            task = asyncio.create_task(source.start(events.append))
            await asyncio.sleep(0.1)
            await source.stop()
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(run())
        assert events == []
