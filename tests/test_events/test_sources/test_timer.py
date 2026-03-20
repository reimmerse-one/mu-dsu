"""Tests for TimerSource."""

import asyncio

from mu_dsu.events.sources.timer import TimerSource
from mu_dsu.events.types import Event


class TestTimerSource:
    def test_emits_events(self):
        events: list[Event] = []
        source = TimerSource(interval=0.02, max_ticks=3)

        asyncio.run(source.start(events.append))
        assert len(events) == 3
        assert all(e.type == "timer.tick" for e in events)

    def test_tick_count(self):
        source = TimerSource(interval=0.01, max_ticks=5)
        asyncio.run(source.start(lambda e: None))
        assert source.tick_count == 5

    def test_custom_event_type(self):
        events: list[Event] = []
        source = TimerSource(interval=0.01, max_ticks=1, event_type="custom.tick")
        asyncio.run(source.start(events.append))
        assert events[0].type == "custom.tick"

    def test_custom_payload(self):
        events: list[Event] = []
        source = TimerSource(
            interval=0.01, max_ticks=1,
            payload_factory=lambda: {"custom": True},
        )
        asyncio.run(source.start(events.append))
        assert events[0].payload == {"custom": True}

    def test_stop(self):
        events: list[Event] = []
        source = TimerSource(interval=0.02)

        async def run():
            task = asyncio.create_task(source.start(events.append))
            await asyncio.sleep(0.07)
            await source.stop()
            await asyncio.sleep(0.05)
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        asyncio.run(run())
        count = len(events)
        assert 1 <= count <= 5  # Should have emitted a few before stopping
